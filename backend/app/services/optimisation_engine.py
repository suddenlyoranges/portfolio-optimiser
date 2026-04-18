"""
Portfolio optimisation engine using Markowitz mean-variance theory.

All functions operate on annualised inputs:
  mu  — 1-D array of expected annual returns, one value per asset
  cov — 2-D covariance matrix of annual returns (n_assets × n_assets)

Weights are long-only and sum to 1 (fully invested, no short-selling).
The risk-free rate (rf) defaults to 2 % per year.
"""

import numpy as np
from scipy.optimize import minimize
from scipy.stats import norm

# ── shared solver config ────────────────────────────────────────────────────

# Every optimisation starts from an equal-weight portfolio and
# keeps each weight in [0, 1] (no leverage, no short-selling).
_WEIGHTS_SUM_TO_ONE = {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}

RISK_FREE_RATE = 0.02  # 2 % annual risk-free rate used across all calculations


# ── helper: portfolio variance ───────────────────────────────────────────────

def _portfolio_variance(weights: np.ndarray, cov: np.ndarray) -> float:
    """Return portfolio variance: w^T · Σ · w."""
    return float(weights @ cov @ weights)


def _portfolio_volatility(weights: np.ndarray, cov: np.ndarray) -> float:
    """Return annualised portfolio volatility (standard deviation)."""
    return float(np.sqrt(_portfolio_variance(weights, cov)))


# ── public: portfolio statistics ─────────────────────────────────────────────

def compute_portfolio_stats(
    weights: np.ndarray,
    mu: np.ndarray,
    cov: np.ndarray,
    rf: float = RISK_FREE_RATE,
) -> dict:
    """
    Return key statistics for a portfolio defined by `weights`.

    Returns a dict with:
      expected_return  — weighted average annual return
      volatility       — annualised standard deviation
      sharpe_ratio     — (return - rf) / volatility
    """
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
    """
    Find the minimum-variance portfolio.

    Ignores expected returns entirely — just minimises portfolio volatility.
    Good when return estimates are unreliable.
    """
    n = len(mu)
    result = minimize(
        fun=_portfolio_variance,
        args=(cov,),
        x0=np.ones(n) / n,
        method="SLSQP",
        bounds=[(0.0, 1.0)] * n,
        constraints=[_WEIGHTS_SUM_TO_ONE],
    )
    if not result.success:
        raise ValueError(f"Optimisation failed: {result.message}")
    return result.x


def max_sharpe(mu: np.ndarray, cov: np.ndarray, rf: float = RISK_FREE_RATE) -> np.ndarray:
    """
    Find the maximum Sharpe ratio portfolio.

    Maximises (expected_return - rf) / volatility, i.e. the best
    risk-adjusted return. This is the most commonly used strategy.
    """
    n = len(mu)

    def negative_sharpe(weights: np.ndarray) -> float:
        annual_return = weights @ mu
        annual_vol = np.sqrt(_portfolio_variance(weights, cov))
        if annual_vol < 1e-10:
            return 1e10  # penalise degenerate portfolios
        return -(annual_return - rf) / annual_vol

    result = minimize(
        fun=negative_sharpe,
        x0=np.ones(n) / n,
        method="SLSQP",
        bounds=[(0.0, 1.0)] * n,
        constraints=[_WEIGHTS_SUM_TO_ONE],
    )
    if not result.success:
        raise ValueError(f"Optimisation failed: {result.message}")
    return result.x


# ── public: efficient frontier ───────────────────────────────────────────────

def _min_variance_for_target_return(
    mu: np.ndarray, cov: np.ndarray, target_return: float
) -> np.ndarray:
    """
    Find the lowest-volatility portfolio that achieves exactly `target_return`.
    Used internally to trace out the efficient frontier.
    """
    n = len(mu)
    result = minimize(
        fun=_portfolio_variance,
        args=(cov,),
        x0=np.ones(n) / n,
        method="SLSQP",
        bounds=[(0.0, 1.0)] * n,
        constraints=[
            _WEIGHTS_SUM_TO_ONE,
            {"type": "eq", "fun": lambda w, t=target_return: w @ mu - t},
        ],
    )
    # Fall back to equal weights if the solver can't satisfy the return target
    return result.x if result.success else np.ones(n) / n


def risk_parity(mu: np.ndarray, cov: np.ndarray) -> np.ndarray:
    """
    Find the risk-parity (equal risk contribution) portfolio.

    Each asset contributes the same fraction of total portfolio volatility.
    Does not use expected returns at all — purely a risk-balancing technique.
    Tends to be more diversified than min-variance when assets are correlated.
    """
    n = len(mu)

    def risk_concentration(weights: np.ndarray) -> float:
        vol = _portfolio_volatility(weights, cov)
        if vol < 1e-10:
            return 1e10
        marginal = cov @ weights / vol          # marginal risk contribution
        contributions = weights * marginal       # actual risk contribution per asset
        target = vol / n                         # equal share for each asset
        return float(np.sum((contributions - target) ** 2))

    result = minimize(
        fun=risk_concentration,
        x0=np.ones(n) / n,
        method="SLSQP",
        bounds=[(1e-6, 1.0)] * n,               # small lower bound avoids zero-weight instability
        constraints=[_WEIGHTS_SUM_TO_ONE],
    )
    if not result.success:
        raise ValueError(f"Optimisation failed: {result.message}")
    return result.x


def equal_weight(mu: np.ndarray, cov: np.ndarray) -> np.ndarray:
    """
    Return an equal-weight portfolio (1/N allocation).

    Every asset receives the same weight regardless of risk or return.
    Often used as a benchmark — surprisingly hard to beat in practice.
    """
    n = len(mu)
    return np.ones(n) / n


def max_diversification(mu: np.ndarray, cov: np.ndarray) -> np.ndarray:
    """
    Find the maximum diversification portfolio.

    Maximises the diversification ratio:
        DR = (w · σ) / sqrt(w^T Σ w)
    where σ is the vector of individual asset volatilities.

    A higher DR means the portfolio is more spread across uncorrelated assets.
    """
    n = len(mu)
    asset_vols = np.sqrt(np.diag(cov))          # individual asset volatilities

    def neg_diversification_ratio(weights: np.ndarray) -> float:
        weighted_avg_vol = float(weights @ asset_vols)
        port_vol = _portfolio_volatility(weights, cov)
        if port_vol < 1e-10:
            return 1e10
        return -weighted_avg_vol / port_vol

    result = minimize(
        fun=neg_diversification_ratio,
        x0=np.ones(n) / n,
        method="SLSQP",
        bounds=[(0.0, 1.0)] * n,
        constraints=[_WEIGHTS_SUM_TO_ONE],
    )
    if not result.success:
        raise ValueError(f"Optimisation failed: {result.message}")
    return result.x


def mean_variance_frontier(mu: np.ndarray, cov: np.ndarray, n_points: int = 100) -> list[dict]:
    """
    Generate the efficient frontier curve.

    Sweeps target returns from the lowest to highest individual-asset return,
    solving for the minimum-variance portfolio at each level.

    Returns a list of {volatility, expected_return} dicts ready for charting.
    """
    target_returns = np.linspace(float(mu.min()), float(mu.max()), n_points)

    frontier = []
    for target in target_returns:
        w = _min_variance_for_target_return(mu, cov, target)
        frontier.append({
            "volatility": _portfolio_volatility(w, cov),
            "expected_return": float(w @ mu),
        })

    return frontier


# ── public: downside risk measures ───────────────────────────────────────────

def compute_var_cvar(
    weights: np.ndarray,
    mu: np.ndarray,
    cov: np.ndarray,
    confidence: float = 0.95,
) -> dict:
    """
    Compute parametric (Gaussian) Value at Risk and Conditional VaR.

    VaR  — the loss not exceeded with probability `confidence` (e.g. 95 %).
    CVaR — the average loss in the worst (1 - confidence) % of outcomes.

    Both are expressed as positive numbers representing losses.
    """
    annual_return = float(weights @ mu)
    annual_vol = _portfolio_volatility(weights, cov)

    # z is the left-tail quantile (negative for losses)
    z = norm.ppf(1 - confidence)
    var = -(annual_return + z * annual_vol)
    cvar = -(annual_return - annual_vol * norm.pdf(z) / (1 - confidence))

    return {"var_95": float(var), "cvar_95": float(cvar)}
