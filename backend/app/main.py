from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, portfolios, assets, optimisation, backtest, market, hedging


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Portfolio Optimiser API",
    version="1.0.0",
    description="Portfolio optimisation, backtesting, and hedging API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(portfolios.router, prefix="/api/v1")
app.include_router(assets.router, prefix="/api/v1")
app.include_router(optimisation.router, prefix="/api/v1")
app.include_router(backtest.router, prefix="/api/v1")
app.include_router(market.router, prefix="/api/v1")
app.include_router(hedging.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok"}
