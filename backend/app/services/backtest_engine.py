from datetime import date

import numpy as np
import pandas as pd


def run_backtest(
    prices: pd.DataFrame,
    weights: dict[str, float],
    start_date: date,
    end_date: date,
    initial_value: float = 100000.0,
    rebalance_frequency: str = "monthly",
) -> dict:
    """
    Run a historical backtest using daily price data.
    Returns dict with 'portfolio_values' (list of {date, value}) and 'metrics'.
    """
    tickers = list(weights.keys())
    prices = prices[tickers].loc[str(start_date):str(end_date)].dropna()

    if prices.empty or len(prices) < 2:
        raise ValueError("Insufficient price data for the given date range and tickers")

    returns = prices.pct_change().dropna()
    w = np.array([weights[t] for t in tickers])

    portfolio_values = []
    current_value = initial_value
    current_weights = w.copy()
    last_rebalance = returns.index[0]

    for dt in returns.index:
        daily_returns = returns.loc[dt].values
        port_return = float(current_weights @ daily_returns)
        current_value *= (1 + port_return)
        portfolio_values.append({
            "date": dt.strftime("%Y-%m-%d"),
            "value": round(current_value, 2),
        })

        # Update weights based on drift
        asset_values = current_weights * (1 + daily_returns)
        total = asset_values.sum()
        if total > 0:
            current_weights = asset_values / total

        # Rebalance check
        if _should_rebalance(last_rebalance, dt, rebalance_frequency):
            current_weights = w.copy()
            last_rebalance = dt

    metrics = _compute_metrics(portfolio_values, initial_value)
    return {
        "portfolio_values": portfolio_values,
        "metrics": metrics,
    }


def _should_rebalance(last: pd.Timestamp, current: pd.Timestamp, frequency: str) -> bool:
    if frequency == "none":
        return False
    if frequency == "monthly":
        return current.month != last.month or current.year != last.year
    if frequency == "quarterly":
        return (current.month - 1) // 3 != (last.month - 1) // 3 or current.year != last.year
    if frequency == "annual":
        return current.year != last.year
    return False


def _compute_metrics(portfolio_values: list[dict], initial_value: float) -> dict:
    values = np.array([pv["value"] for pv in portfolio_values])
    dates = pd.to_datetime([pv["date"] for pv in portfolio_values])

    final_value = values[-1]
    total_return = (final_value - initial_value) / initial_value

    # Daily returns from portfolio values
    daily_returns = np.diff(values) / values[:-1]
    ann_vol = float(np.std(daily_returns) * np.sqrt(252))

    # Sharpe ratio (assuming rf = 0.02 annualised)
    rf_daily = 0.02 / 252
    excess = daily_returns - rf_daily
    sharpe = float(np.mean(excess) / np.std(excess) * np.sqrt(252)) if np.std(excess) > 0 else 0.0

    # Max drawdown
    cummax = np.maximum.accumulate(values)
    drawdowns = (values - cummax) / cummax
    max_dd = float(np.min(drawdowns))

    # Max drawdown duration
    dd_duration = 0
    max_dd_duration = 0
    for i in range(len(values)):
        if values[i] < cummax[i]:
            dd_duration += 1
            max_dd_duration = max(max_dd_duration, dd_duration)
        else:
            dd_duration = 0

    return {
        "total_return": round(total_return, 6),
        "annualised_volatility": round(ann_vol, 6),
        "sharpe_ratio": round(sharpe, 4),
        "max_drawdown": round(max_dd, 6),
        "max_drawdown_duration_days": max_dd_duration,
    }
