"""
Beta hedging module using statsmodels OLS regression.

Computes the hedge ratio between a portfolio and a benchmark index
using ordinary least squares, providing beta, R², and hedge notional.
"""

from datetime import date, timedelta

import numpy as np
import statsmodels.api as sm

from app.services.market_data_service import compute_returns, fetch_prices


async def compute_beta_hedge(
    portfolio_weights: dict[str, float],
    benchmark_ticker: str,
    lookback_days: int,
    portfolio_value: float,
    db=None,
) -> dict:
    """
    Compute beta hedge: OLS regression of portfolio returns vs benchmark.
    Returns beta, R-squared, hedge ratio, and hedge notional.
    """
    tickers = list(portfolio_weights.keys())
    all_tickers = tickers + [benchmark_ticker]

    end_date = date.today()
    start_date = end_date - timedelta(days=int(lookback_days * 1.5))

    prices = await fetch_prices(all_tickers, start_date, end_date, db=db)
    returns = compute_returns(prices)

    if len(returns) < 20:
        raise ValueError("Insufficient data for beta calculation")

    # Compute portfolio returns
    w = np.array([portfolio_weights[t] for t in tickers])
    portfolio_returns = returns[tickers].values @ w
    benchmark_returns = returns[benchmark_ticker].values

    # OLS regression via statsmodels: portfolio_return = alpha + beta * benchmark_return
    X = sm.add_constant(benchmark_returns)
    model = sm.OLS(portfolio_returns, X).fit()

    beta = float(model.params[1])
    r_squared = float(model.rsquared)

    # Hedge notional
    hedge_notional = abs(beta) * portfolio_value

    if r_squared > 0.7:
        strength = "strong"
    elif r_squared > 0.4:
        strength = "moderate"
    else:
        strength = "weak"

    recommendation = (
        f"Short ${hedge_notional:,.0f} of {benchmark_ticker} "
        f"(beta={beta:.3f}) to hedge the portfolio. "
        f"R²={r_squared:.3f} indicates {strength} "
        f"correlation with {benchmark_ticker}."
    )

    return {
        "beta": round(beta, 4),
        "r_squared": round(r_squared, 4),
        "hedge_ratio": round(abs(beta), 4),
        "hedge_notional": round(hedge_notional, 2),
        "benchmark_ticker": benchmark_ticker,
        "recommendation": recommendation,
    }
