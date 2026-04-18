from datetime import date, timedelta

from fastapi import APIRouter, Query

from app.services import market_data_service as market

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/search")
async def search_tickers(q: str = Query(min_length=1, max_length=20)):
    results = market.search_ticker(q)
    return results


@router.get("/info/{ticker}")
async def get_info(ticker: str):
    try:
        info = market.get_ticker_info(ticker)
        return info
    except Exception as e:
        return {"error": str(e)}


@router.get("/prices/{ticker}")
async def get_prices(
    ticker: str,
    start: date | None = None,
    end: date | None = None,
):
    if end is None:
        end = date.today()
    if start is None:
        start = end - timedelta(days=365)

    prices = await market.fetch_prices([ticker], start, end)
    records = [
        {"date": dt.strftime("%Y-%m-%d"), "price": round(float(p), 2)}
        for dt, p in zip(prices.index, prices[ticker])
    ]
    return records
