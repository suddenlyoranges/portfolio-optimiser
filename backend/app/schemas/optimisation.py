import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class OptimisationMethod(str, Enum):
    MIN_VARIANCE = "min_variance"
    MAX_SHARPE = "max_sharpe"
    MEAN_VARIANCE = "mean_variance"
    RISK_PARITY = "risk_parity"
    MAX_DIVERSIFICATION = "max_diversification"
    EQUAL_WEIGHT = "equal_weight"


class OptimisationRequest(BaseModel):
    method: OptimisationMethod = OptimisationMethod.MAX_SHARPE
    use_historical: bool = True
    lookback_days: int = Field(252, ge=30, le=2520)


class PortfolioStats(BaseModel):
    expected_return: float
    volatility: float
    sharpe_ratio: float
    var_95: float | None = None
    cvar_95: float | None = None


class FrontierPoint(BaseModel):
    volatility: float
    expected_return: float


class OptimisationResponse(BaseModel):
    id: uuid.UUID
    portfolio_id: uuid.UUID
    method: str
    weights: dict[str, float]
    stats: PortfolioStats
    frontier: list[FrontierPoint] = []
    created_at: datetime

    model_config = {"from_attributes": True}
