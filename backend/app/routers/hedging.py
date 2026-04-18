import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.optimisation import OptimisationResult
from app.models.portfolio import Portfolio
from app.models.user import User
from app.schemas.hedging import BetaHedgeRequest, BetaHedgeResponse
from app.services import hedging_module

router = APIRouter(prefix="/hedge", tags=["hedging"])


@router.post("/{portfolio_id}/beta", response_model=BetaHedgeResponse)
async def compute_beta_hedge(
    portfolio_id: uuid.UUID,
    body: BetaHedgeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(OptimisationResult)
        .join(Portfolio)
        .where(Portfolio.id == portfolio_id, Portfolio.user_id == user.id)
        .order_by(OptimisationResult.created_at.desc())
        .limit(1)
    )
    opt = result.scalar_one_or_none()
    if not opt:
        raise HTTPException(
            status_code=404,
            detail="No optimisation results found. Run optimisation first.",
        )

    hedge = await hedging_module.compute_beta_hedge(
        portfolio_weights=opt.weights,
        benchmark_ticker=body.benchmark_ticker,
        lookback_days=body.lookback_days,
        portfolio_value=body.portfolio_value,
        db=db,
    )
    return BetaHedgeResponse(**hedge)
