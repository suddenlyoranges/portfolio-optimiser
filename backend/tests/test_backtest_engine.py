from datetime import date

import numpy as np
import pandas as pd
import pytest

from app.services.backtest_engine import run_backtest


@pytest.fixture
def sample_prices():
    """Create synthetic price data for 3 assets over 100 trading days."""
    np.random.seed(42)
    dates = pd.bdate_range(start="2023-01-01", periods=100)
    data = {}
    for ticker, start_price in [("AAPL", 150), ("MSFT", 250), ("GOOGL", 100)]:
        returns = np.random.normal(0.0005, 0.02, 100)
        prices = start_price * np.cumprod(1 + returns)
        data[ticker] = prices
    return pd.DataFrame(data, index=dates)


class TestRunBacktest:
    def test_basic_backtest(self, sample_prices):
        weights = {"AAPL": 0.4, "MSFT": 0.35, "GOOGL": 0.25}
        result = run_backtest(
            prices=sample_prices,
            weights=weights,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 6, 30),
            initial_value=100000.0,
            rebalance_frequency="monthly",
        )
        assert "portfolio_values" in result
        assert "metrics" in result
        assert len(result["portfolio_values"]) > 0

    def test_metrics_structure(self, sample_prices):
        weights = {"AAPL": 0.5, "MSFT": 0.3, "GOOGL": 0.2}
        result = run_backtest(
            prices=sample_prices,
            weights=weights,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 6, 30),
        )
        m = result["metrics"]
        assert "total_return" in m
        assert "annualised_volatility" in m
        assert "sharpe_ratio" in m
        assert "max_drawdown" in m
        assert "max_drawdown_duration_days" in m

    def test_max_drawdown_negative(self, sample_prices):
        weights = {"AAPL": 0.5, "MSFT": 0.3, "GOOGL": 0.2}
        result = run_backtest(
            prices=sample_prices,
            weights=weights,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 6, 30),
        )
        assert result["metrics"]["max_drawdown"] <= 0

    def test_no_rebalance(self, sample_prices):
        weights = {"AAPL": 0.5, "MSFT": 0.3, "GOOGL": 0.2}
        result = run_backtest(
            prices=sample_prices,
            weights=weights,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 6, 30),
            rebalance_frequency="none",
        )
        assert len(result["portfolio_values"]) > 0
