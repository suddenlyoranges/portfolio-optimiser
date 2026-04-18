import uuid
from datetime import date, timedelta

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.portfolio import Portfolio, PortfolioAsset
from app.models.user import User
from app.schemas.portfolio import (
    AssetInPortfolio,
    PortfolioCreate,
    PortfolioListResponse,
    PortfolioResponse,
    PortfolioUpdate,
)
from app.services.market_data_service import fetch_prices, compute_returns
from app.services.optimisation_engine import compute_portfolio_stats

router = APIRouter(prefix="/portfolios", tags=["portfolios"])


@router.get("/", response_model=list[PortfolioListResponse])
async def list_portfolios(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Portfolio)
        .where(Portfolio.user_id == user.id)
        .order_by(Portfolio.created_at.desc())
    )
    portfolios = result.scalars().all()

    response = []
    for p in portfolios:
        count_result = await db.execute(
            select(func.count(PortfolioAsset.id)).where(PortfolioAsset.portfolio_id == p.id)
        )
        count = count_result.scalar()
        response.append(
            PortfolioListResponse(
                id=p.id,
                name=p.name,
                description=p.description,
                asset_count=count,
                created_at=p.created_at,
            )
        )
    return response


@router.post("/", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    body: PortfolioCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    portfolio = Portfolio(user_id=user.id, name=body.name, description=body.description)
    db.add(portfolio)
    await db.commit()
    await db.refresh(portfolio)
    return PortfolioResponse(
        id=portfolio.id,
        name=portfolio.name,
        description=portfolio.description,
        created_at=portfolio.created_at,
        updated_at=portfolio.updated_at,
        assets=[],
    )


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(
    portfolio_id: uuid.UUID,
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

    assets = [
        AssetInPortfolio(
            id=pa.asset.id,
            ticker=pa.asset.ticker,
            name=pa.asset.name,
            sector=pa.asset.sector,
            manual_expected_return=pa.manual_expected_return,
            manual_volatility=pa.manual_volatility,
            shares=pa.shares,
        )
        for pa in portfolio.assets
    ]
    return PortfolioResponse(
        id=portfolio.id,
        name=portfolio.name,
        description=portfolio.description,
        created_at=portfolio.created_at,
        updated_at=portfolio.updated_at,
        assets=assets,
    )


@router.put("/{portfolio_id}", response_model=PortfolioResponse)
async def update_portfolio(
    portfolio_id: uuid.UUID,
    body: PortfolioUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Portfolio).where(Portfolio.id == portfolio_id, Portfolio.user_id == user.id)
    )
    portfolio = result.scalar_one_or_none()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    if body.name is not None:
        portfolio.name = body.name
    if body.description is not None:
        portfolio.description = body.description

    await db.commit()
    await db.refresh(portfolio)
    return PortfolioResponse(
        id=portfolio.id,
        name=portfolio.name,
        description=portfolio.description,
        created_at=portfolio.created_at,
        updated_at=portfolio.updated_at,
        assets=[],
    )


@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio(
    portfolio_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Portfolio).where(Portfolio.id == portfolio_id, Portfolio.user_id == user.id)
    )
    portfolio = result.scalar_one_or_none()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    await db.delete(portfolio)
    await db.commit()


@router.get("/{portfolio_id}/metrics")
async def portfolio_metrics(
    portfolio_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Compute live performance metrics for a portfolio using current prices."""
    result = await db.execute(
        select(Portfolio)
        .options(selectinload(Portfolio.assets).selectinload(PortfolioAsset.asset))
        .where(Portfolio.id == portfolio_id, Portfolio.user_id == user.id)
    )
    portfolio = result.scalar_one_or_none()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    if not portfolio.assets:
        raise HTTPException(status_code=400, detail="Portfolio has no assets")

    tickers = [pa.asset.ticker for pa in portfolio.assets]
    shares_map = {pa.asset.ticker: pa.shares or 0 for pa in portfolio.assets}
    sector_map = {pa.asset.ticker: pa.asset.sector or "Unknown" for pa in portfolio.assets}

    # Fetch 1 year of prices
    end_date = date.today()
    start_date = end_date - timedelta(days=380)
    try:
        prices = await fetch_prices(tickers, start_date, end_date, db=db)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Could not fetch price data. Check that all tickers are valid market symbols.",
        )

    # Drop tickers with no price data
    available = [t for t in tickers if t in prices.columns and prices[t].notna().sum() > 0]
    if not available:
        raise HTTPException(
            status_code=400,
            detail="No price data found for any ticker. Ensure your tickers are valid market symbols (e.g. AAPL, MSFT).",
        )
    missing = set(tickers) - set(available)
    prices = prices[available]

    returns = compute_returns(prices)

    if len(returns) < 20:
        raise HTTPException(status_code=400, detail="Insufficient price data to compute metrics")

    # Latest prices for valuation
    latest_prices = {t: float(prices[t].iloc[-1]) for t in available}

    # Total portfolio value
    total_value = sum(shares_map[t] * latest_prices[t] for t in available)

    # Weights by market value (fall back to equal-weight if no shares entered)
    if total_value > 0:
        weights_dict = {t: (shares_map[t] * latest_prices[t]) / total_value for t in available}
    else:
        n = len(available)
        weights_dict = {t: 1.0 / n for t in available}

    w = np.array([weights_dict[t] for t in available])

    # Annualised mean returns and covariance
    mu = returns[available].mean().values * 252
    cov = returns[available].cov().values * 252

    stats = compute_portfolio_stats(w, mu, cov)

    # Diversification score: 1 - (portfolio_vol / weighted_avg_vol)
    asset_vols = np.sqrt(np.diag(cov))
    weighted_avg_vol = float(w @ asset_vols)
    div_score = round(1.0 - stats["volatility"] / weighted_avg_vol, 4) if weighted_avg_vol > 0 else 0.0

    # Volatility label
    vol_pct = stats["volatility"] * 100
    if vol_pct < 10:
        vol_label = "Low"
    elif vol_pct < 20:
        vol_label = "Moderate"
    else:
        vol_label = "High"

    # Sharpe label
    sr = stats["sharpe_ratio"]
    if sr >= 1.0:
        sharpe_label = "Excellent"
    elif sr >= 0.5:
        sharpe_label = "Good"
    else:
        sharpe_label = "Poor"

    # Asset allocation
    asset_allocation = [
        {"ticker": t, "weight": round(weights_dict[t], 4), "value": round(shares_map[t] * latest_prices[t], 2)}
        for t in available
    ]

    # Sector allocation
    sector_totals: dict[str, float] = {}
    for t in available:
        s = sector_map[t]
        sector_totals[s] = sector_totals.get(s, 0) + weights_dict[t]
    sector_allocation = [
        {"sector": s, "weight": round(w, 4)}
        for s, w in sorted(sector_totals.items(), key=lambda x: -x[1])
    ]

    return {
        "expected_return": round(stats["expected_return"], 4),
        "volatility": round(stats["volatility"], 4),
        "volatility_label": vol_label,
        "sharpe_ratio": round(stats["sharpe_ratio"], 4),
        "sharpe_label": sharpe_label,
        "diversification_score": div_score,
        "total_value": round(total_value, 2),
        "asset_allocation": asset_allocation,
        "sector_allocation": sector_allocation,
        "missing_tickers": sorted(missing),
    }
