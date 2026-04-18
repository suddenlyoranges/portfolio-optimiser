import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class PortfolioCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)


class PortfolioUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)


class AssetInPortfolio(BaseModel):
    id: uuid.UUID
    ticker: str
    name: str | None
    sector: str | None = None
    manual_expected_return: float | None
    manual_volatility: float | None
    shares: int | None = None

    model_config = {"from_attributes": True}


class PortfolioResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime
    assets: list[AssetInPortfolio] = []

    model_config = {"from_attributes": True}


class PortfolioListResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    asset_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}
