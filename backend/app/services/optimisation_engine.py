"""
Portfolio optimisation engine using PyPortfolioOpt.

Wraps the pypfopt library to provide:
  - min_variance, max_sharpe, risk_parity, max_diversification, equal_weight
  - efficient frontier generation
  - VaR / CVaR computation

All functions accept annualised mu (1-D array) and cov (2-D matrix)
and return weight arrays compatible with the rest of the application.
"""

import numpy as np
import pandas as pd
from pypfopt import EfficientFrontier, risk_models, expected_returns
from pypfopt import objective_functions
from scipy.stats import norm

RISK_FREE_RATE = 0.02  # 2 % annual risk-free rate


# ── internal helpers ─────────────────────────────────────────────────────────

def _arrays_to_pd(mu: np.ndarray, cov: np.ndarray):
    """Convert raw numpy arrays into pandas Series/DataFrame for pypfopt."""
    n = len(mu)
    labels = [str(i) for i in range(n)]
    return pd.Series(mu, index=labels), pd.DataFrame(cov, index=labels, columns=labels)


def _ordered_weights(ef: EfficientFrontier, n: int) -> np.ndarray:
    """Extract cleaned weights from an EfficientFrontier as a numpy array."""
    cleaned: dict[str, float] = ef.clean_weights(cutoff=1e-4)  # type: ignore[assignment]
    labels = [str(i) for i in range(n)]
    return np.array([cleaned.get(l, 0.0) for l in labels])


def _portfolio_volatility(weights: np.ndarray, cov: np.ndarray) -> float:
    """Return annualised portfolio volatility."""
    return float(np.sqrt(weights @ cov @ weights))


# ── public: portfolio statistics ─────────────────────────────────────────────

def compute_portfolio_stats(
    weights: np.ndarray,
    mu: np.ndarray,
    cov: np.ndarray,
    rf: float = RISK_FREE_RATE,
) -> dict:
    """Return expected_return, volatility, and sharpe_ratio for given weights."""
    annual_return = float(weights @ mu)
    annual_vol = _portfolio_volatility(weights, cov)
    sharpe = (annual_return - rf) / annual_vol if annual_vol > 0 else 0.0
    return {
        "expected_return": annual_return,
        "volatility": annual_vol,
        "sharpe_ratio": sharpe,
    }


# ── public: optimisation strategies ──────────────────────────────────────────

def min_variance(mu: np.ndarray, cov: np.ndarray) -> np.ndarray:
    """Find the minimum-variance portfolio using PyPortfolioOpt."""
    mu_s, cov_df = _arrays_to_pd(mu, cov)
    ef = EfficientFrontier(mu_s, cov_df, weight_bounds=(0, 1))
    ef.min_volatility()
    return _ordered_weights(ef, len(mu))


def max_sharpe(mu: np.ndarray, cov: np.ndarray, rf: float = RISK_FREE_RATE) -> np.ndarray:
    """Find the maximum Sharpe ratio portfolio using PyPortfolioOpt."""
    mu_s, cov_df = _arrays_to_pd(mu, cov)
    ef = EfficientFrontier(mu_s, cov_df, weight_bounds=(0, 1))
    ef.max_sharpe(risk_free_rate=rf)
    return _ordered_weights(ef, len(mu))


def risk_parity(mu: np.ndarray, cov: np.ndarray) -> np.ndarray:
    """Find the risk-parity (equal risk contribution) portfolio using PyPortfolioOpt."""
    mu_s, cov_df = _arrays_to_pd(mu, cov)
    ef = EfficientFrontier(mu_s, cov_df, weight_bounds=(0, 1))
    ef.min_volatility()
    # Re-optimise with L2 regularisation toward equal weight to approximate risk parity
    ef2 = EfficientFrontier(mu_s, cov_df, weight_bounds=(0, 1))
    ef2.add_objective(objective_functions.L2_reg, gamma=2)
    ef2.min_volatility()
    return _ordered_weights(ef2, len(mu))


def equal_weight(mu: np.ndarray, cov: np.ndarray) -> np.ndarray:
    """Return an equal-weight portfolio (1/N allocation)."""
    n = len(mu)
    return np.ones(n) / n


def max_diversification(mu: np.ndarray, cov: np.ndarray) -> np.ndarray:
    """
    Find the maximum diversification portfolio.

    Maximises diversification ratio: (w · σ) / sqrt(w^T Σ w)
    Implemented via PyPortfolioOpt's EfficientFrontier with a custom objective.
    """
    mu_s, cov_df = _arrays_to_pd(mu, cov)
    n = len(mu)
    asset_vols = np.sqrt(np.diag(cov))

    ef = EfficientFrontier(mu_s, cov_df, weight_bounds=(0, 1))

    def neg_diversification(w, cov_matrix):
        w = np.array(list(w.values())) if isinstance(w, dict) else np.array(w)
        weighted_avg_vol = float(w @ asset_vols)
        port_vol = float(np.sqrt(w @ cov @ w))
        if port_vol < 1e-10:
            return 1e10
        return -weighted_avg_vol / port_vol

    ef.convex_objective(neg_diversification, cov_matrix=cov)
    return _ordered_weights(ef, n)


# ── public: efficient frontier ───────────────────────────────────────────────

def mean_variance_frontier(mu: np.ndarray, cov: np.ndarray, n_points: int = 100) -> list[dict]:
    """Generate the efficient frontier curve using PyPortfolioOpt."""
    mu_s, cov_df = _arrays_to_pd(mu, cov)
    frontier = []
    target_returns = np.linspace(float(mu.min()), float(mu.max()), n_points)

    for target in target_returns:
        try:
            ef = EfficientFrontier(mu_s, cov_df, weight_bounds=(0, 1))
            ef.efficient_return(target_return=target)
            w = _ordered_weights(ef, len(mu))
            frontier.append({
                "volatility": _portfolio_volatility(w, cov),
                "expected_return": float(w @ mu),
            })
        except Exception:
            # Skip infeasible target returns
            continue

    return frontier


# ── public: downside risk measures ───────────────────────────────────────────

def compute_var_cvar(
    weights: np.ndarray,
    mu: np.ndarray,
    cov: np.ndarray,
    confidence: float = 0.95,
) -> dict:
    """Compute parametric (Gaussian) Value at Risk and Conditional VaR."""
    annual_return = float(weights @ mu)
    annual_vol = _portfolio_volatility(weights, cov)

    z = norm.ppf(1 - confidence)
    var = -(annual_return + z * annual_vol)
    cvar = -(annual_return - annual_vol * norm.pdf(z) / (1 - confidence))

    return {"var_95": float(var), "cvar_95": float(cvar)}
