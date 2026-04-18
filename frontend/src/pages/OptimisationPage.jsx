import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import {
  runOptimisation,
  listOptimisations,
  getOptimisationResult,
  exportOptimisationCsv,
} from "../api/optimisation";
import { getPortfolio } from "../api/portfolios";
import EfficientFrontierChart from "../components/charts/EfficientFrontierChart";
import AllocationPieChart from "../components/charts/AllocationPieChart";
import Loading from "../components/common/Loading";
import InfoTip from "../components/common/InfoTip";
import styles from "./optimisation.module.css";

export default function OptimisationPage() {
  const { id } = useParams();
  const [portfolio, setPortfolio] = useState(null);
  const [method, setMethod] = useState("max_sharpe");
  const [useHistorical, setUseHistorical] = useState(true);
  const [lookbackDays, setLookbackDays] = useState("252");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [pageLoading, setPageLoading] = useState(true);
  const [error, setError] = useState("");
  const [savedResults, setSavedResults] = useState([]);

  useEffect(() => {
    Promise.all([getPortfolio(id), listOptimisations(id)])
      .then(([pRes, hRes]) => {
        setPortfolio(pRes.data);
        setSavedResults(hRes.data);
      })
      .catch(() => setError("Failed to load portfolio"))
      .finally(() => setPageLoading(false));
  }, [id]);

  const handleOptimise = async () => {
    setError("");
    setLoading(true);
    try {
      const res = await runOptimisation(id, {
        method,
        use_historical: useHistorical,
        lookback_days: parseInt(lookbackDays),
      });
      setResult(res.data);
      const histRes = await listOptimisations(id);
      setSavedResults(histRes.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Optimisation failed");
    } finally {
      setLoading(false);
    }
  };

  const loadSavedResult = async (resultId) => {
    setError("");
    setLoading(true);
    try {
      const res = await getOptimisationResult(resultId);
      setResult(res.data);
    } catch {
      setError("Failed to load saved result");
    } finally {
      setLoading(false);
    }
  };

  const handleExportCsv = async (resultId) => {
    try {
      const res = await exportOptimisationCsv(resultId);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = `optimisation_${resultId}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch {
      setError("Failed to export CSV");
    }
  };

  if (pageLoading) return <Loading />;

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1>Optimise: {portfolio?.name}</h1>
        <Link to={`/portfolio/${id}`} className={styles.backLink}>
          &larr; Back to portfolio
        </Link>
      </div>

      {error && <div className={styles.error}>{error}</div>}

      <div className={styles.controls}>
        <div className={styles.field}>
          <label>
            Method
            <InfoTip text="Max Sharpe = best return per unit of risk. Min Variance = lowest overall risk. Risk Parity = each asset contributes equally to risk. Max Diversification = maximises spread across uncorrelated assets." />
          </label>
          <select value={method} onChange={(e) => setMethod(e.target.value)}>
            <option value="max_sharpe">Max Sharpe Ratio</option>
            <option value="min_variance">Minimum Variance</option>
            <option value="risk_parity">Risk Parity</option>
            <option value="max_diversification">Max Diversification</option>
            <option value="equal_weight">Equal Weight (1/N)</option>
          </select>
        </div>
        <div className={styles.field}>
          <label>Data Source</label>
          <select
            value={useHistorical}
            onChange={(e) => setUseHistorical(e.target.value === "true")}
          >
            <option value="true">Historical (yfinance)</option>
            <option value="false">Manual inputs</option>
          </select>
        </div>
        {useHistorical && (
          <div className={styles.field}>
            <label>Lookback (days)</label>
            <input
              type="number"
              value={lookbackDays}
              onChange={(e) => setLookbackDays(e.target.value)}
            />
          </div>
        )}
        <button
          className={styles.runBtn}
          onClick={handleOptimise}
          disabled={loading}
        >
          {loading ? "Running..." : "Run Optimisation"}
        </button>
      </div>

      {result && (
        <div className={styles.results}>
          <div className={styles.resultsHeader}>
            <h2>Results</h2>
            <button
              className={styles.exportBtn}
              onClick={() => handleExportCsv(result.id)}
            >
              Export CSV
            </button>
          </div>
          <div className={styles.statsGrid}>
            <div className={styles.statCard}>
              <span className={styles.statLabel}>
                Expected Return
                <InfoTip text="The average yearly gain you'd expect from this portfolio, based on past data." />
              </span>
              <span className={styles.statValue}>
                {(result.stats.expected_return * 100).toFixed(2)}%
              </span>
            </div>
            <div className={styles.statCard}>
              <span className={styles.statLabel}>
                Volatility
                <InfoTip text="How much the portfolio's value tends to swing up and down. Lower means steadier." />
              </span>
              <span className={styles.statValue}>
                {(result.stats.volatility * 100).toFixed(2)}%
              </span>
            </div>
            <div className={styles.statCard}>
              <span className={styles.statLabel}>
                Sharpe Ratio
                <InfoTip text="Reward per unit of risk. Higher is better — it means more return for each unit of uncertainty." />
              </span>
              <span className={styles.statValue}>
                {result.stats.sharpe_ratio.toFixed(3)}
              </span>
            </div>
            <div className={styles.statCard}>
              <span className={styles.statLabel}>
                VaR (95%)
                <InfoTip text="Value at Risk — the most you'd expect to lose on 95% of days. Think of it as a 'bad day' estimate." />
              </span>
              <span className={styles.statValue}>
                {result.stats.var_95 != null
                  ? `${(result.stats.var_95 * 100).toFixed(2)}%`
                  : "\u2014"}
              </span>
            </div>
            <div className={styles.statCard}>
              <span className={styles.statLabel}>
                CVaR (95%)
                <InfoTip text="Conditional VaR — the average loss on the worst 5% of days. A deeper look at tail risk beyond VaR." />
              </span>
              <span className={styles.statValue}>
                {result.stats.cvar_95 != null
                  ? `${(result.stats.cvar_95 * 100).toFixed(2)}%`
                  : "\u2014"}
              </span>
            </div>
          </div>

          <div className={styles.chartRow}>
            <div className={styles.chartCard}>
              <h3>
                Efficient Frontier
                <InfoTip text="A curve showing the best possible return you can get for each level of risk. Points on the line are 'optimal' portfolios." />
              </h3>
              <EfficientFrontierChart
                frontier={result.frontier}
                optimal={{
                  volatility: result.stats.volatility,
                  expected_return: result.stats.expected_return,
                }}
              />
            </div>
            <div className={styles.chartCard}>
              <h3>
                Portfolio Allocation
                <InfoTip text="How your money is split across different stocks. Each slice is the percentage invested in that stock." />
              </h3>
              <AllocationPieChart weights={result.weights} />
            </div>
          </div>

          <div className={styles.weightsCard}>
            <h3>Optimal Weights</h3>
            <table className={styles.weightsTable}>
              <thead>
                <tr>
                  <th>Ticker</th>
                  <th>Weight</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(result.weights)
                  .sort(([, a], [, b]) => b - a)
                  .map(([ticker, weight]) => (
                    <tr key={ticker}>
                      <td>{ticker}</td>
                      <td>{(weight * 100).toFixed(2)}%</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {savedResults.length > 0 && (
        <div className={styles.savedSection}>
          <h2>Saved Optimisations</h2>
          <table className={styles.savedTable}>
            <thead>
              <tr>
                <th>Date</th>
                <th>Method</th>
                <th>Return</th>
                <th>Volatility</th>
                <th>Sharpe</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {savedResults.map((r) => (
                <tr
                  key={r.id}
                  className={result?.id === r.id ? styles.activeRow : ""}
                >
                  <td>{new Date(r.created_at).toLocaleDateString()}</td>
                  <td>
                    {{
                      max_sharpe: "Max Sharpe",
                      min_variance: "Min Variance",
                      risk_parity: "Risk Parity",
                      max_diversification: "Max Diversification",
                    }[r.method] ?? r.method}
                  </td>
                  <td>{(r.stats.expected_return * 100).toFixed(2)}%</td>
                  <td>{(r.stats.volatility * 100).toFixed(2)}%</td>
                  <td>{r.stats.sharpe_ratio.toFixed(3)}</td>
                  <td className={styles.savedActions}>
                    <button
                      className={styles.viewBtn}
                      onClick={() => loadSavedResult(r.id)}
                    >
                      View
                    </button>
                    <button
                      className={styles.exportBtnSmall}
                      onClick={() => handleExportCsv(r.id)}
                    >
                      CSV
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
