import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { computeBetaHedge } from "../api/hedging";
import { getPortfolio } from "../api/portfolios";
import Loading from "../components/common/Loading";
import InfoTip from "../components/common/InfoTip";
import styles from "./hedging.module.css";

export default function HedgingPage() {
  const { id } = useParams();
  const [portfolio, setPortfolio] = useState(null);
  const [benchmark, setBenchmark] = useState("SPY");
  const [lookback, setLookback] = useState("252");
  const [portfolioValue, setPortfolioValue] = useState("100000");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [pageLoading, setPageLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getPortfolio(id)
      .then((res) => setPortfolio(res.data))
      .catch(() => setError("Failed to load portfolio"))
      .finally(() => setPageLoading(false));
  }, [id]);

  const handleCompute = async () => {
    setError("");
    setLoading(true);
    try {
      const res = await computeBetaHedge(id, {
        benchmark_ticker: benchmark.toUpperCase(),
        lookback_days: parseInt(lookback),
        portfolio_value: parseFloat(portfolioValue),
      });
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Hedge computation failed");
    } finally {
      setLoading(false);
    }
  };

  if (pageLoading) return <Loading />;

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1>Hedging: {portfolio?.name}</h1>
        <Link to={`/portfolio/${id}`} className={styles.backLink}>
          &larr; Back to portfolio
        </Link>
      </div>

      {error && <div className={styles.error}>{error}</div>}

      <div className={styles.controls}>
        <h3>
          Beta Hedge Analysis
          <InfoTip text="Figures out how much your portfolio moves with the overall market, and how to offset that exposure." />
        </h3>
        <div className={styles.fieldRow}>
          <div className={styles.field}>
            <label>
              Benchmark
              <InfoTip text="The market index to compare against (e.g. SPY tracks the S&P 500)." />
            </label>
            <input
              value={benchmark}
              onChange={(e) => setBenchmark(e.target.value)}
            />
          </div>
          <div className={styles.field}>
            <label>
              Lookback (days)
              <InfoTip text="How many trading days of history to analyse. 252 ≈ one year." />
            </label>
            <input
              type="number"
              value={lookback}
              onChange={(e) => setLookback(e.target.value)}
            />
          </div>
          <div className={styles.field}>
            <label>Portfolio Value ($)</label>
            <input
              type="number"
              value={portfolioValue}
              onChange={(e) => setPortfolioValue(e.target.value)}
            />
          </div>
          <button
            className={styles.runBtn}
            onClick={handleCompute}
            disabled={loading}
          >
            {loading ? "Computing..." : "Compute Hedge"}
          </button>
        </div>
      </div>

      {result && (
        <div className={styles.results}>
          <div className={styles.metricsGrid}>
            <div className={styles.metricCard}>
              <span className={styles.metricLabel}>
                Portfolio Beta
                <InfoTip text="How much your portfolio moves when the market moves. Beta 1 = moves with the market; above 1 = more volatile; below 1 = less volatile." />
              </span>
              <span className={styles.metricValue}>
                {result.beta.toFixed(3)}
              </span>
            </div>
            <div className={styles.metricCard}>
              <span className={styles.metricLabel}>
                R²
                <InfoTip text="How well the benchmark explains your portfolio's movements. 1.0 = perfectly correlated, 0 = no relationship." />
              </span>
              <span className={styles.metricValue}>
                {result.r_squared.toFixed(3)}
              </span>
            </div>
            <div className={styles.metricCard}>
              <span className={styles.metricLabel}>
                Hedge Ratio
                <InfoTip text="The fraction of your portfolio to short in the benchmark to neutralise market risk." />
              </span>
              <span className={styles.metricValue}>
                {result.hedge_ratio.toFixed(3)}
              </span>
            </div>
            <div className={styles.metricCard}>
              <span className={styles.metricLabel}>
                Hedge Notional
                <InfoTip text="The dollar amount of the benchmark you'd need to short-sell to hedge your portfolio." />
              </span>
              <span className={styles.metricValue}>
                ${result.hedge_notional.toLocaleString()}
              </span>
            </div>
          </div>

          <div className={styles.recommendation}>
            <h3>Recommendation</h3>
            <p>{result.recommendation}</p>
          </div>
        </div>
      )}
    </div>
  );
}
