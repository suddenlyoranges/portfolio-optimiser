import uuid
from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class RebalanceFrequency(str, Enum):
    NONE = "none"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class BacktestRequest(BaseModel):
    optimisation_result_id: uuid.UUID
    start_date: date
    end_date: date
    rebalance_frequency: RebalanceFrequency = RebalanceFrequency.MONTHLY
    initial_value: float = Field(100000.0, gt=0)


class BacktestMetrics(BaseModel):
    model_config = {"extra": "ignore"}

    total_return: float
    annualised_volatility: float
    sharpe_ratio: float
    max_drawdown: float
    max_drawdown_duration_days: int


class BacktestResponse(BaseModel):
    id: uuid.UUID
    portfolio_id: uuid.UUID
    optimisation_result_id: uuid.UUID | None
    start_date: date
    end_date: date
    rebalancing_frequency: str
    portfolio_values: list[dict]
    metrics: BacktestMetrics
    created_at: datetime

    model_config = {"from_attributes": True}
