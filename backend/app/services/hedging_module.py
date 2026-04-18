from datetime import date, timedelta

import numpy as np

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

    # OLS regression: portfolio_return = alpha + beta * benchmark_return
    x_mat = np.column_stack([np.ones(len(benchmark_returns)), benchmark_returns])
    coeffs = np.linalg.lstsq(x_mat, portfolio_returns, rcond=None)[0]
    beta = float(coeffs[1])

    # R-squared
    predicted = x_mat @ coeffs
    ss_res = np.sum((portfolio_returns - predicted) ** 2)
    ss_tot = np.sum((portfolio_returns - portfolio_returns.mean()) ** 2)
    r_squared = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0

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
