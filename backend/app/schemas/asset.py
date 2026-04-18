import uuid

from pydantic import BaseModel, Field


class AssetAdd(BaseModel):
    ticker: str = Field(min_length=1, max_length=20)
    manual_expected_return: float | None = None
    manual_volatility: float | None = None
    shares: int | None = None


class AssetResponse(BaseModel):
    id: uuid.UUID
    ticker: str
    name: str | None
    asset_type: str | None
    sector: str | None

    model_config = {"from_attributes": True}


class CsvRow(BaseModel):
    ticker: str
    shares: int | None = None
    expected_return: float | None = None
    volatility: float | None = None
