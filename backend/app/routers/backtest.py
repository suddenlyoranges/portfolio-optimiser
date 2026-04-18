import uuid
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.backtest import BacktestResult
from app.models.optimisation import OptimisationResult
from app.models.portfolio import Portfolio
from app.models.user import User
from app.schemas.backtest import BacktestMetrics, BacktestRequest, BacktestResponse
from app.services import backtest_engine
from app.services import market_data_service as market

router = APIRouter(prefix="/backtest", tags=["backtest"])


@router.post("/{portfolio_id}", response_model=BacktestResponse)
async def run_backtest(
    portfolio_id: uuid.UUID,
    body: BacktestRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Portfolio).where(Portfolio.id == portfolio_id, Portfolio.user_id == user.id)
    )
    portfolio = result.scalar_one_or_none()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    result = await db.execute(
        select(OptimisationResult).where(
            OptimisationResult.id == body.optimisation_result_id,
            OptimisationResult.portfolio_id == portfolio_id,
        )
    )
    opt_result = result.scalar_one_or_none()
    if not opt_result:
        raise HTTPException(status_code=404, detail="Optimisation result not found")

    weights = opt_result.weights
    tickers = list(weights.keys())

    start_with_buffer = body.start_date - timedelta(days=5)
    prices = await market.fetch_prices(tickers, start_with_buffer, body.end_date, db=db)

    bt = backtest_engine.run_backtest(
        prices=prices,
        weights=weights,
        start_date=body.start_date,
        end_date=body.end_date,
        initial_value=body.initial_value,
        rebalance_frequency=body.rebalance_frequency.value,
    )

    bt_result = BacktestResult(
        portfolio_id=portfolio_id,
        optimisation_result_id=opt_result.id,
        start_date=body.start_date,
        end_date=body.end_date,
        rebalancing_frequency=body.rebalance_frequency.value,
        portfolio_values=bt["portfolio_values"],
        metrics=bt["metrics"],
    )
    db.add(bt_result)
    await db.commit()
    await db.refresh(bt_result)

    return BacktestResponse(
        id=bt_result.id,
        portfolio_id=portfolio_id,
        optimisation_result_id=opt_result.id,
        start_date=bt_result.start_date,
        end_date=bt_result.end_date,
        rebalancing_frequency=bt_result.rebalancing_frequency,
        portfolio_values=bt["portfolio_values"],
        metrics=BacktestMetrics(**bt["metrics"]),
        created_at=bt_result.created_at,
    )


@router.get("/results/{result_id}", response_model=BacktestResponse)
async def get_backtest_result(
    result_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BacktestResult)
        .join(Portfolio)
        .where(BacktestResult.id == result_id, Portfolio.user_id == user.id)
    )
    bt = result.scalar_one_or_none()
    if not bt:
        raise HTTPException(status_code=404, detail="Backtest result not found")

    return BacktestResponse(
        id=bt.id,
        portfolio_id=bt.portfolio_id,
        optimisation_result_id=bt.optimisation_result_id,
        start_date=bt.start_date,
        end_date=bt.end_date,
        rebalancing_frequency=bt.rebalancing_frequency,
        portfolio_values=bt.portfolio_values,
        metrics=BacktestMetrics(**bt.metrics),
        created_at=bt.created_at,
    )
