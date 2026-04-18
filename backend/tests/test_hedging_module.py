from unittest.mock import AsyncMock, patch

import numpy as np
import pandas as pd
import pytest

from app.services.hedging_module import compute_beta_hedge


@pytest.fixture
def mock_prices():
    """Create synthetic price data for portfolio assets + benchmark."""
    np.random.seed(42)
    dates = pd.bdate_range(start="2022-01-01", periods=252)
    benchmark_returns = np.random.normal(0.0004, 0.012, 252)
    benchmark_prices = 400 * np.cumprod(1 + benchmark_returns)
    data = {"SPY": benchmark_prices}
    for ticker, beta_true in [("AAPL", 1.2), ("MSFT", 1.1)]:
        asset_returns = beta_true * benchmark_returns + np.random.normal(0, 0.005, 252)
        data[ticker] = 150 * np.cumprod(1 + asset_returns)
    return pd.DataFrame(data, index=dates)


@pytest.mark.asyncio
class TestBetaHedge:
    async def test_result_structure(self, mock_prices):
        with patch(
            "app.services.hedging_module.fetch_prices",
            new_callable=AsyncMock,
            return_value=mock_prices,
        ):
            result = await compute_beta_hedge(
                portfolio_weights={"AAPL": 0.6, "MSFT": 0.4},
                benchmark_ticker="SPY",
                lookback_days=252,
                portfolio_value=100000.0,
            )
        assert "beta" in result
        assert "r_squared" in result
        assert "hedge_ratio" in result
        assert "hedge_notional" in result
        assert "benchmark_ticker" in result
        assert "recommendation" in result

    async def test_beta_is_positive(self, mock_prices):
        with patch(
            "app.services.hedging_module.fetch_prices",
            new_callable=AsyncMock,
            return_value=mock_prices,
        ):
            result = await compute_beta_hedge(
                portfolio_weights={"AAPL": 0.6, "MSFT": 0.4},
                benchmark_ticker="SPY",
                lookback_days=252,
                portfolio_value=100000.0,
            )
        assert result["beta"] > 0

    async def test_r_squared_range(self, mock_prices):
        with patch(
            "app.services.hedging_module.fetch_prices",
            new_callable=AsyncMock,
            return_value=mock_prices,
        ):
            result = await compute_beta_hedge(
                portfolio_weights={"AAPL": 0.6, "MSFT": 0.4},
                benchmark_ticker="SPY",
                lookback_days=252,
                portfolio_value=100000.0,
            )
        assert 0.0 <= result["r_squared"] <= 1.0
