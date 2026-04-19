import uuid
from datetime import date, timedelta
import csv
import io

import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.optimisation import OptimisationResult
from app.models.portfolio import Portfolio, PortfolioAsset
from app.models.user import User
from app.schemas.optimisation import (
    FrontierPoint,
    OptimisationMethod,
    OptimisationRequest,
    OptimisationResponse,
    PortfolioStats,
)
from app.services import market_data_service as market
from app.services import optimisation_engine as engine

router = APIRouter(prefix="/optimise", tags=["optimisation"])


@router.post("/{portfolio_id}", response_model=OptimisationResponse)
async def run_optimisation(
    portfolio_id: uuid.UUID,
    body: OptimisationRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Portfolio)
        .options(selectinload(Portfolio.assets).selectinload(PortfolioAsset.asset))
        .where(Portfolio.id == portfolio_id, Portfolio.user_id == user.id)
    )
    portfolio = result.scalar_one_or_none()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    if len(portfolio.assets) < 2:
        raise HTTPException(status_code=400, detail="Portfolio must have at least 2 assets")

    tickers = [pa.asset.ticker for pa in portfolio.assets]

    if body.use_historical:
        end_date = date.today()
        start_date = end_date - timedelta(days=int(body.lookback_days * 1.5))
        prices = await market.fetch_prices(tickers, start_date, end_date, db=db)
        returns = market.compute_returns(prices)
        mu = market.compute_expected_returns(returns)
        cov = market.compute_covariance_matrix(returns)
    else:
        mu_list = []
        vol_list = []
        for pa in portfolio.assets:
            if pa.manual_expected_return is None or pa.manual_volatility is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"Manual expected return and volatility required for {pa.asset.ticker}",
                )
            mu_list.append(pa.manual_expected_return)
            vol_list.append(pa.manual_volatility)

        mu = np.array(mu_list)
        cov = np.diag(np.array(vol_list) ** 2)

    # Run optimisation
    rf = body.risk_free_rate
    if body.method == OptimisationMethod.MIN_VARIANCE:
        weights = engine.min_variance(mu, cov)
    elif body.method == OptimisationMethod.MAX_SHARPE:
        weights = engine.max_sharpe(mu, cov, rf=rf)
    elif body.method == OptimisationMethod.RISK_PARITY:
        weights = engine.risk_parity(mu, cov)
    elif body.method == OptimisationMethod.MAX_DIVERSIFICATION:
        weights = engine.max_diversification(mu, cov)
    elif body.method == OptimisationMethod.EQUAL_WEIGHT:
        weights = engine.equal_weight(mu, cov)
    else:
        weights = engine.max_sharpe(mu, cov, rf=rf)

    stats = engine.compute_portfolio_stats(weights, mu, cov, rf=rf)
    risk = engine.compute_var_cvar(weights, mu, cov)
    frontier = engine.mean_variance_frontier(mu, cov)

    weights_dict = {t: round(float(w), 6) for t, w in zip(tickers, weights)}

    opt_result = OptimisationResult(
        portfolio_id=portfolio.id,
        method=body.method.value,
        weights=weights_dict,
        expected_return=stats["expected_return"],
        volatility=stats["volatility"],
        sharpe_ratio=stats["sharpe_ratio"],
        var_95=risk["var_95"],
        cvar_95=risk["cvar_95"],
        frontier_data=frontier,
    )
    db.add(opt_result)
    await db.commit()
    await db.refresh(opt_result)

    return OptimisationResponse(
        id=opt_result.id,
        portfolio_id=portfolio.id,
        method=opt_result.method,
        weights=weights_dict,
        stats=PortfolioStats(
            expected_return=stats["expected_return"],
            volatility=stats["volatility"],
            sharpe_ratio=stats["sharpe_ratio"],
            var_95=risk["var_95"],
            cvar_95=risk["cvar_95"],
        ),
        frontier=[FrontierPoint(**p) for p in frontier],
        created_at=opt_result.created_at,
    )


@router.get("/results/{result_id}", response_model=OptimisationResponse)
async def get_result(
    result_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(OptimisationResult)
        .join(Portfolio)
        .where(OptimisationResult.id == result_id, Portfolio.user_id == user.id)
    )
    opt = result.scalar_one_or_none()
    if not opt:
        raise HTTPException(status_code=404, detail="Result not found")

    frontier = opt.frontier_data or []
    return OptimisationResponse(
        id=opt.id,
        portfolio_id=opt.portfolio_id,
        method=opt.method,
        weights=opt.weights,
        stats=PortfolioStats(
            expected_return=opt.expected_return,
            volatility=opt.volatility,
            sharpe_ratio=opt.sharpe_ratio,
            var_95=opt.var_95,
            cvar_95=opt.cvar_95,
        ),
        frontier=[FrontierPoint(**p) for p in frontier],
        created_at=opt.created_at,
    )


@router.get("/history/{portfolio_id}", response_model=list[OptimisationResponse])
async def list_optimisations(
    portfolio_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Portfolio).where(Portfolio.id == portfolio_id, Portfolio.user_id == user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Portfolio not found")

    result = await db.execute(
        select(OptimisationResult)
        .where(OptimisationResult.portfolio_id == portfolio_id)
        .order_by(OptimisationResult.created_at.desc())
    )
    rows = result.scalars().all()

    return [
        OptimisationResponse(
            id=opt.id,
            portfolio_id=opt.portfolio_id,
            method=opt.method,
            weights=opt.weights,
            stats=PortfolioStats(
                expected_return=opt.expected_return,
                volatility=opt.volatility,
                sharpe_ratio=opt.sharpe_ratio,
                var_95=opt.var_95,
                cvar_95=opt.cvar_95,
            ),
            frontier=[],
            created_at=opt.created_at,
        )
        for opt in rows
    ]


@router.get("/results/{result_id}/csv")
async def export_csv(
    result_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(OptimisationResult)
        .join(Portfolio)
        .where(OptimisationResult.id == result_id, Portfolio.user_id == user.id)
    )
    opt = result.scalar_one_or_none()
    if not opt:
        raise HTTPException(status_code=404, detail="Result not found")

    buf = io.StringIO()
    writer = csv.writer(buf)

    writer.writerow(["Portfolio Optimisation Report"])
    writer.writerow(["Method", opt.method])
    writer.writerow(["Date", opt.created_at.strftime("%Y-%m-%d %H:%M")])
    writer.writerow(["Expected Return", f"{opt.expected_return:.6f}"])
    writer.writerow(["Volatility", f"{opt.volatility:.6f}"])
    writer.writerow(["Sharpe Ratio", f"{opt.sharpe_ratio:.6f}"])
    if opt.var_95 is not None:
        writer.writerow(["VaR (95%)", f"{opt.var_95:.6f}"])
    if opt.cvar_95 is not None:
        writer.writerow(["CVaR (95%)", f"{opt.cvar_95:.6f}"])
    writer.writerow([])
    writer.writerow(["Ticker", "Weight"])
    for ticker, weight in sorted(opt.weights.items(), key=lambda x: -x[1]):
        writer.writerow([ticker, f"{weight:.6f}"])

    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=optimisation_{result_id}.csv"},
    )
