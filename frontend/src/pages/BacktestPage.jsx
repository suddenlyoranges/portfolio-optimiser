import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { runBacktest } from "../api/backtest";
import { runOptimisation } from "../api/optimisation";
import { getPortfolio } from "../api/portfolios";
import BacktestLineChart from "../components/charts/BacktestLineChart";
import Loading from "../components/common/Loading";
import InfoTip from "../components/common/InfoTip";
import styles from "./backtest.module.css";

export default function BacktestPage() {
  const { id } = useParams();
  const [portfolio, setPortfolio] = useState(null);
  const [optimisationId, setOptimisationId] = useState("");
  const [startDate, setStartDate] = useState("2022-01-01");
  const [endDate, setEndDate] = useState("2024-01-01");
  const [frequency, setFrequency] = useState("monthly");
  const [initialValue, setInitialValue] = useState("100000");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [pageLoading, setPageLoading] = useState(true);
  const [error, setError] = useState("");
  const [optHint, setOptHint] = useState("");

  useEffect(() => {
    getPortfolio(id)
      .then((res) => setPortfolio(res.data))
      .catch(() => setError("Failed to load portfolio"))
      .finally(() => setPageLoading(false));
  }, [id]);

  const handleRunOptFirst = async () => {
    setError("");
    setOptHint("Running optimisation first...");
    try {
      const res = await runOptimisation(id, {
        method: "max_sharpe",
        risk_free_rate: 0.02,
        use_historical: true,
        lookback_days: 252,
      });
      setOptimisationId(res.data.id);
      setOptHint(`Optimisation complete (ID: ${res.data.id.slice(0, 8)}...)`);
    } catch (err) {
      setError(err.response?.data?.detail || "Optimisation failed");
      setOptHint("");
    }
  };

  const handleBacktest = async () => {
    if (!optimisationId) {
      setError("Run optimisation first or enter an optimisation result ID");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const res = await runBacktest(id, {
        optimisation_result_id: optimisationId,
        start_date: startDate,
        end_date: endDate,
        rebalance_frequency: frequency,
        initial_value: parseFloat(initialValue),
      });
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Backtest failed");
    } finally {
      setLoading(false);
    }
  };

  if (pageLoading) return <Loading />;

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1>Backtest: {portfolio?.name}</h1>
        <Link to={`/portfolio/${id}`} className={styles.backLink}>
          &larr; Back to portfolio
        </Link>
      </div>

      {error && <div className={styles.error}>{error}</div>}

      <div className={styles.controls}>
        <div className={styles.optRow}>
          <p className={styles.hint}>
            {optimisationId
              ? `Using optimisation: ${optimisationId.slice(0, 8)}...`
              : "No optimisation selected."}
          </p>
          <button className={styles.optBtn} onClick={handleRunOptFirst}>
            Run Max-Sharpe Optimisation
            <InfoTip text="Optimize for best risk-adjusted returns. Favors assets with high return relative to risk." />
          </button>
          {optHint && <span className={styles.optHint}>{optHint}</span>}
        </div>

        <div className={styles.fieldRow}>
          <div className={styles.field}>
            <label>Start Date</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
          </div>
          <div className={styles.field}>
            <label>End Date</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
            />
          </div>
          <div className={styles.field}>
            <label>
              Rebalancing
              <InfoTip text="How often the portfolio is adjusted back to its target stock mix. Without it, winning stocks grow to dominate." />
            </label>
            <select
              value={frequency}
              onChange={(e) => setFrequency(e.target.value)}
            >
              <option value="none">None</option>
              <option value="monthly">Monthly</option>
              <option value="quarterly">Quarterly</option>
              <option value="annual">Annual</option>
            </select>
          </div>
          <div className={styles.field}>
            <label>Initial Value ($)</label>
            <input
              type="number"
              value={initialValue}
              onChange={(e) => setInitialValue(e.target.value)}
            />
          </div>
          <button
            className={styles.runBtn}
            onClick={handleBacktest}
            disabled={loading}
          >
            {loading ? "Running..." : "Run Backtest"}
          </button>
        </div>
      </div>

      {result && (
        <div className={styles.results}>
          <div className={styles.metricsGrid}>
            {[
              [
                "Total Return",
                `${(result.metrics.total_return * 100).toFixed(2)}%`,
                "The overall gain or loss over the entire backtest period.",
              ],
              [
                "Volatility",
                `${(result.metrics.annualised_volatility * 100).toFixed(2)}%`,
                "How much the portfolio's value swung up and down each year. Lower means calmer.",
              ],
              [
                "Sharpe",
                result.metrics.sharpe_ratio.toFixed(3),
                "Return earned per unit of risk. Higher is better.",
              ],
              [
                "Max Drawdown",
                `${(result.metrics.max_drawdown * 100).toFixed(2)}%`,
                "The biggest peak-to-trough drop. Think of it as the worst losing streak.",
              ],
              [
                "DD Duration",
                `${result.metrics.max_drawdown_duration_days}d`,
                "Drawdown Duration — how many days it took to recover from the worst drop.",
              ],
            ].map(([label, value, tip]) => (
              <div key={label} className={styles.metricCard}>
                <span className={styles.metricLabel}>
                  {label}
                  <InfoTip text={tip} />
                </span>
                <span className={styles.metricValue}>{value}</span>
              </div>
            ))}
          </div>

          <div className={styles.chartCard}>
            <h3>
              Portfolio Value Over Time
              <InfoTip text="Shows how your investment would have grown (or shrunk) day by day over the backtest period." />
            </h3>
            <BacktestLineChart data={result.portfolio_values} />
          </div>
        </div>
      )}
    </div>
  );
}
