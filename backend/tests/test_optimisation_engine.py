import numpy as np
import pytest

from app.services.optimisation_engine import (
    compute_portfolio_stats,
    compute_var_cvar,
    max_sharpe,
    mean_variance_frontier,
    min_variance,
)

# Sample data: 3 assets
MU = np.array([0.10, 0.15, 0.12])
COV = np.array([
    [0.04, 0.006, 0.002],
    [0.006, 0.09, 0.009],
    [0.002, 0.009, 0.01],
])
RF = 0.02


class TestComputePortfolioStats:
    def test_equal_weights(self):
        w = np.array([1 / 3, 1 / 3, 1 / 3])
        stats = compute_portfolio_stats(w, MU, COV, RF)
        assert 0.0 < stats["expected_return"] < 1.0
        assert stats["volatility"] > 0
        assert isinstance(stats["sharpe_ratio"], float)

    def test_single_asset(self):
        w = np.array([1.0, 0.0, 0.0])
        stats = compute_portfolio_stats(w, MU, COV, RF)
        assert abs(stats["expected_return"] - 0.10) < 1e-6
        assert abs(stats["volatility"] - 0.2) < 1e-6


class TestMinVariance:
    def test_weights_sum_to_one(self):
        w = min_variance(MU, COV)
        assert abs(np.sum(w) - 1.0) < 1e-6

    def test_long_only(self):
        w = min_variance(MU, COV)
        assert np.all(w >= -1e-8)

    def test_lower_vol_than_equal_weight(self):
        w_mv = min_variance(MU, COV)
        w_eq = np.ones(3) / 3
        vol_mv = np.sqrt(w_mv @ COV @ w_mv)
        vol_eq = np.sqrt(w_eq @ COV @ w_eq)
        assert vol_mv <= vol_eq + 1e-8


class TestMaxSharpe:
    def test_weights_sum_to_one(self):
        w = max_sharpe(MU, COV, RF)
        assert abs(np.sum(w) - 1.0) < 1e-6

    def test_long_only(self):
        w = max_sharpe(MU, COV, RF)
        assert np.all(w >= -1e-8)

    def test_higher_sharpe_than_equal_weight(self):
        w_ms = max_sharpe(MU, COV, RF)
        w_eq = np.ones(3) / 3
        s_ms = compute_portfolio_stats(w_ms, MU, COV, RF)["sharpe_ratio"]
        s_eq = compute_portfolio_stats(w_eq, MU, COV, RF)["sharpe_ratio"]
        assert s_ms >= s_eq - 1e-6


class TestFrontier:
    def test_returns_sufficient_points(self):
        frontier = mean_variance_frontier(MU, COV, n_points=50)
        assert len(frontier) >= 10  # some targets may be infeasible

    def test_frontier_point_structure(self):
        frontier = mean_variance_frontier(MU, COV, n_points=10)
        for point in frontier:
            assert "volatility" in point
            assert "expected_return" in point


class TestVarCvar:
    def test_var_cvar_positive(self):
        w = np.ones(3) / 3
        result = compute_var_cvar(w, MU, COV)
        assert isinstance(result["var_95"], float)
        assert isinstance(result["cvar_95"], float)

    def test_cvar_gte_var(self):
        w = np.ones(3) / 3
        result = compute_var_cvar(w, MU, COV)
        assert result["cvar_95"] >= result["var_95"] - 1e-6
