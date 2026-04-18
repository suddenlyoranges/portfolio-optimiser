from datetime import date

import numpy as np
import pandas as pd
import yfinance as yf
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.price_cache import PriceCache


async def fetch_prices(
    tickers: list[str],
    start_date: date,
    end_date: date,
    db: AsyncSession | None = None,
) -> pd.DataFrame:
    """Fetch adjusted close prices for tickers. Caches results when db is provided."""
    df = yf.download(
        tickers,
        start=start_date.isoformat(),
        end=end_date.isoformat(),
        auto_adjust=True,
        progress=False,
    )
    if df.empty:
        raise ValueError(f"No price data returned for {tickers}")

    if isinstance(df.columns, pd.MultiIndex):
        prices = df["Close"]
    else:
        prices = df[["Close"]].rename(columns={"Close": tickers[0]})

    prices = prices.dropna()

    if db is not None:
        await _cache_prices(prices, db)

    return prices


async def _cache_prices(prices: pd.DataFrame, db: AsyncSession) -> None:
    rows = []
    for ticker in prices.columns:
        for dt, price in prices[ticker].items():
            if pd.notna(price):
                rows.append({
                    "ticker": ticker,
                    "date": dt.date() if hasattr(dt, "date") else dt,
                    "close_price": float(price),
                })
    if rows:
        batch_size = 2000
        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            stmt = insert(PriceCache).values(batch).on_conflict_do_nothing(constraint="uq_ticker_date")
            await db.execute(stmt)
        await db.commit()


def compute_returns(prices: pd.DataFrame) -> pd.DataFrame:
    return prices.pct_change().dropna()


def compute_expected_returns(returns: pd.DataFrame, annualise: bool = True) -> np.ndarray:
    mu = returns.mean().to_numpy(copy=True).astype(float)
    if annualise:
        mu *= 252
    return mu


def compute_covariance_matrix(returns: pd.DataFrame, annualise: bool = True) -> np.ndarray:
    cov = returns.cov().to_numpy(copy=True).astype(float)
    if annualise:
        cov *= 252
    return cov


def search_ticker(query: str) -> list[dict]:
    """Search for tickers matching a query string."""
    try:
        ticker = yf.Ticker(query.upper())
        info = ticker.info
        if info and info.get("symbol"):
            return [{
                "ticker": info.get("symbol", query.upper()),
                "name": info.get("longName") or info.get("shortName", ""),
                "asset_type": info.get("quoteType", ""),
                "sector": info.get("sector", ""),
            }]
    except Exception:
        pass
    return []


def get_ticker_info(ticker_symbol: str) -> dict:
    ticker = yf.Ticker(ticker_symbol.upper())
    info = ticker.info
    return {
        "ticker": info.get("symbol", ticker_symbol.upper()),
        "name": info.get("longName") or info.get("shortName", ""),
        "asset_type": info.get("quoteType", ""),
        "sector": info.get("sector", ""),
        "currency": info.get("currency", ""),
        "exchange": info.get("exchange", ""),
        "market_cap": info.get("marketCap"),
        "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
    }
