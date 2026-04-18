from pydantic import BaseModel, Field


class BetaHedgeRequest(BaseModel):
    benchmark_ticker: str = "SPY"
    lookback_days: int = Field(252, ge=30, le=2520)
    portfolio_value: float = Field(100000.0, gt=0)


class BetaHedgeResponse(BaseModel):
    beta: float
    r_squared: float
    hedge_ratio: float
    hedge_notional: float
    benchmark_ticker: str
    recommendation: str
