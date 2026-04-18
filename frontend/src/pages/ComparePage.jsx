import { useState, useEffect } from "react";
import { listPortfolios } from "../api/portfolios";
import { runOptimisation } from "../api/optimisation";
import RiskReturnScatter from "../components/charts/RiskReturnScatter";
import Loading from "../components/common/Loading";
import InfoTip from "../components/common/InfoTip";
import styles from "./compare.module.css";

export default function ComparePage() {
  const [portfolios, setPortfolios] = useState([]);
  const [selected, setSelected] = useState([]);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pageLoading, setPageLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    listPortfolios()
      .then((res) => setPortfolios(res.data))
      .catch(() => setError("Failed to load portfolios"))
      .finally(() => setPageLoading(false));
  }, []);

  const togglePortfolio = (id) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id],
    );
  };

  const handleCompare = async () => {
    setError("");
    setLoading(true);
    setResults([]);
    try {
      const optimised = await Promise.all(
        selected.map(async (pid) => {
          const res = await runOptimisation(pid, {
            method: "max_sharpe",
            risk_free_rate: 0.02,
            use_historical: true,
            lookback_days: 252,
          });
          const p = portfolios.find((x) => x.id === pid);
          return {
            name: p?.name || pid,
            volatility: res.data.stats.volatility,
            expectedReturn: res.data.stats.expected_return,
            sharpe: res.data.stats.sharpe_ratio,
            weights: res.data.weights,
          };
        }),
      );
      setResults(optimised);
    } catch (err) {
      setError(err.response?.data?.detail || "Comparison failed");
    } finally {
      setLoading(false);
    }
  };

  if (pageLoading) return <Loading />;

  return (
    <div className={styles.page}>
      <h1>Compare Portfolios</h1>

      {error && <div className={styles.error}>{error}</div>}

      <div className={styles.selectSection}>
        <p>
          Select portfolios to compare (max-Sharpe optimisation will be run for
          each):
        </p>
        <div className={styles.checkboxes}>
          {portfolios.map((p) => (
            <label key={p.id} className={styles.checkbox}>
              <input
                type="checkbox"
                checked={selected.includes(p.id)}
                onChange={() => togglePortfolio(p.id)}
              />
              {p.name} ({p.asset_count} assets)
            </label>
          ))}
        </div>
        <button
          className={styles.compareBtn}
          onClick={handleCompare}
          disabled={selected.length < 2 || loading}
        >
          {loading ? "Comparing..." : `Compare ${selected.length} Portfolios`}
        </button>
      </div>

      {results.length > 0 && (
        <div className={styles.results}>
          <div className={styles.chartCard}>
            <h3>
              Risk vs Return
              <InfoTip text="Each dot is a portfolio. Further right = more risk, higher up = more return. Ideal is top-left." />
            </h3>
            <RiskReturnScatter portfolios={results} />
          </div>

          <div className={styles.tableCard}>
            <h3>Comparison Table</h3>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Portfolio</th>
                  <th>
                    Return
                    <InfoTip text="Expected yearly gain." />
                  </th>
                  <th>
                    Volatility
                    <InfoTip text="How much the value swings. Lower = steadier." />
                  </th>
                  <th>
                    Sharpe
                    <InfoTip text="Return per unit of risk. Higher is better." />
                  </th>
                </tr>
              </thead>
              <tbody>
                {results.map((r) => (
                  <tr key={r.name}>
                    <td className={styles.nameCell}>{r.name}</td>
                    <td>{(r.expectedReturn * 100).toFixed(2)}%</td>
                    <td>{(r.volatility * 100).toFixed(2)}%</td>
                    <td>{r.sharpe.toFixed(3)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
