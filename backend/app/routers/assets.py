import csv
import io
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.asset import Asset
from app.models.portfolio import Portfolio, PortfolioAsset
from app.models.user import User
from app.schemas.asset import AssetResponse

router = APIRouter(prefix="/portfolios/{portfolio_id}/assets", tags=["assets"])


async def _get_user_portfolio(
    portfolio_id: uuid.UUID, user: User, db: AsyncSession
) -> Portfolio:
    result = await db.execute(
        select(Portfolio).where(Portfolio.id == portfolio_id, Portfolio.user_id == user.id)
    )
    portfolio = result.scalar_one_or_none()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio


@router.post("/", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def add_asset(
    portfolio_id: uuid.UUID,
    body: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    portfolio = await _get_user_portfolio(portfolio_id, user, db)

    ticker = body.get("ticker", "").strip().upper()
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker is required")

    # Find or create asset
    name = body.get("name", "").strip() or None

    result = await db.execute(select(Asset).where(Asset.ticker == ticker))
    asset = result.scalar_one_or_none()
    if not asset:
        asset = Asset(ticker=ticker, name=name)
        db.add(asset)
        await db.flush()
    elif name and not asset.name:
        asset.name = name

    # Check for duplicate
    existing = await db.execute(
        select(PortfolioAsset).where(
            PortfolioAsset.portfolio_id == portfolio.id,
            PortfolioAsset.asset_id == asset.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Asset {ticker} already in portfolio")

    pa = PortfolioAsset(
        portfolio_id=portfolio.id,
        asset_id=asset.id,
        manual_expected_return=body.get("manual_expected_return"),
        manual_volatility=body.get("manual_volatility"),
        shares=body.get("shares"),
    )
    db.add(pa)
    await db.commit()
    await db.refresh(asset)
    return asset


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_asset(
    portfolio_id: uuid.UUID,
    asset_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    portfolio = await _get_user_portfolio(portfolio_id, user, db)

    result = await db.execute(
        select(PortfolioAsset).where(
            PortfolioAsset.portfolio_id == portfolio.id,
            PortfolioAsset.asset_id == asset_id,
        )
    )
    pa = result.scalar_one_or_none()
    if not pa:
        raise HTTPException(status_code=404, detail="Asset not in portfolio")

    await db.delete(pa)
    await db.commit()


@router.post("/csv", status_code=status.HTTP_201_CREATED)
async def upload_csv(
    portfolio_id: uuid.UUID,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a CSV with columns: ticker, expected_return (optional), volatility (optional)."""
    portfolio = await _get_user_portfolio(portfolio_id, user, db)

    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    content = await file.read()
    text = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))

    added = []
    for row in reader:
        ticker = row.get("ticker", "").strip().upper()
        if not ticker:
            continue

        csv_name = row.get("name", "").strip() or None

        result = await db.execute(select(Asset).where(Asset.ticker == ticker))
        asset = result.scalar_one_or_none()
        if not asset:
            asset = Asset(ticker=ticker, name=csv_name)
            db.add(asset)
            await db.flush()
        elif csv_name and not asset.name:
            asset.name = csv_name

        existing = await db.execute(
            select(PortfolioAsset).where(
                PortfolioAsset.portfolio_id == portfolio.id,
                PortfolioAsset.asset_id == asset.id,
            )
        )
        if existing.scalar_one_or_none():
            continue

        shares_str = row.get("shares", "").strip()
        exp_ret = row.get("expected_return", "").strip()
        vol = row.get("volatility", "").strip()

        pa = PortfolioAsset(
            portfolio_id=portfolio.id,
            asset_id=asset.id,
            shares=int(shares_str) if shares_str else None,
            manual_expected_return=float(exp_ret) if exp_ret else None,
            manual_volatility=float(vol) if vol else None,
        )
        db.add(pa)
        added.append(ticker)

    await db.commit()
    return {"added": added, "count": len(added)}
