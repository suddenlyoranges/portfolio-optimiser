import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import {
  getPortfolio,
  addAsset,
  removeAsset,
  uploadCsv,
  getPortfolioMetrics,
} from "../api/portfolios";
import AssetTable from "../components/portfolio/AssetTable";
import AllocationPieChart from "../components/charts/AllocationPieChart";
import CsvUpload from "../components/portfolio/CsvUpload";
import InfoTip from "../components/common/InfoTip";
import Loading from "../components/common/Loading";
import styles from "./portfolio.module.css";

export default function PortfolioPage() {
  const { id } = useParams();
  const [portfolio, setPortfolio] = useState(null);
  const [ticker, setTicker] = useState("");
  const [name, setName] = useState("");
  const [shares, setShares] = useState("");
  const [expReturn, setExpReturn] = useState("");
  const [vol, setVol] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [metrics, setMetrics] = useState(null);
  const [metricsLoading, setMetricsLoading] = useState(false);
  const [metricsError, setMetricsError] = useState("");

  const load = async () => {
    try {
      const res = await getPortfolio(id);
      setPortfolio(res.data);
      if (res.data.assets?.length > 0) {
        loadMetrics();
      }
    } catch {
      setError("Failed to load portfolio");
    } finally {
      setLoading(false);
    }
  };

  const loadMetrics = async () => {
    setMetricsLoading(true);
    setMetricsError("");
    try {
      const res = await getPortfolioMetrics(id);
      setMetrics(res.data);
    } catch (err) {
      setMetrics(null);
      setMetricsError(
        err.response?.data?.detail || "Could not load portfolio metrics",
      );
    } finally {
      setMetricsLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [id]);

  const handleAddAsset = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await addAsset(id, {
        ticker: ticker.toUpperCase(),
        name: name.trim() || null,
        shares: shares ? parseInt(shares) : null,
        manual_expected_return: expReturn ? parseFloat(expReturn) : null,
        manual_volatility: vol ? parseFloat(vol) : null,
      });
      setTicker("");
      setName("");
      setShares("");
      setExpReturn("");
      setVol("");
      load();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to add asset");
    }
  };

  const handleRemove = async (assetId) => {
    try {
      await removeAsset(id, assetId);
      load();
    } catch {
      setError("Failed to remove asset");
    }
  };

  const handleCsv = async (file) => {
    try {
      await uploadCsv(id, file);
      load();
    } catch (err) {
      setError(err.response?.data?.detail || "CSV upload failed");
    }
  };

  if (loading) return <Loading />;
  if (!portfolio) return <p>Portfolio not found</p>;

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <div>
          <h1>{portfolio.name}</h1>
          {portfolio.description && (
            <p className={styles.desc}>{portfolio.description}</p>
          )}
        </div>
        <div className={styles.actions}>
          <Link to={`/portfolio/${id}/optimise`} className={styles.actionBtn}>
            Optimise
          </Link>
          <Link to={`/portfolio/${id}/backtest`} className={styles.actionBtn}>
            Backtest
          </Link>
          <Link
            to={`/portfolio/${id}/hedge`}
            className={styles.actionBtnOutline}
          >
            Hedge
          </Link>
        </div>
      </div>

      {error && <div className={styles.error}>{error}</div>}

      {metrics && (
        <div className={styles.metricsSection}>
          <h2>Portfolio Performance Metrics</h2>
          {metrics.missing_tickers?.length > 0 && (
            <p className={styles.metricsHint}>
              No price data for: {metrics.missing_tickers.join(", ")} — these
              tickers are excluded from metrics.
            </p>
          )}
          <div className={styles.metricsGrid}>
            <div className={styles.metricCard}>
              <span className={styles.metricLabel}>
                Expected Annual Return
                <InfoTip text="The average yearly gain you'd expect, based on the last year of data." />
              </span>
              <span className={styles.metricValue}>
                {(metrics.expected_return * 100).toFixed(2)}%
              </span>
            </div>
            <div className={styles.metricCard}>
              <span className={styles.metricLabel}>
                Portfolio Risk (Volatility)
                <InfoTip text="How much the portfolio's value tends to swing. Lower = calmer." />
              </span>
              <span className={styles.metricValue}>
                {(metrics.volatility * 100).toFixed(2)}%
              </span>
              <span className={styles.metricSub}>
                {metrics.volatility_label}
              </span>
            </div>
            <div className={styles.metricCard}>
              <span className={styles.metricLabel}>
                Sharpe Ratio
                <InfoTip text="Return earned per unit of risk. Above 1 is excellent." />
              </span>
              <span className={styles.metricValue}>
                {metrics.sharpe_ratio.toFixed(2)}
              </span>
              <span className={styles.metricSub}>{metrics.sharpe_label}</span>
            </div>
            <div className={styles.metricCard}>
              <span className={styles.metricLabel}>
                Diversification Score
                <InfoTip text="How much risk is reduced by combining assets. Higher = more benefit from diversification." />
              </span>
              <span className={styles.metricValue}>
                {(metrics.diversification_score * 100).toFixed(0)}%
              </span>
            </div>
            {metrics.total_value > 0 && (
              <div className={styles.metricCard}>
                <span className={styles.metricLabel}>
                  Total Portfolio Value
                  <InfoTip text="Current market value based on shares held and latest prices." />
                </span>
                <span className={styles.metricValue}>
                  ${metrics.total_value.toLocaleString()}
                </span>
              </div>
            )}
          </div>
          <div className={styles.chartRow}>
            <div className={styles.chartCard}>
              <h3>Asset Allocation</h3>
              {(() => {
                const w = {};
                metrics.asset_allocation.forEach((a) => {
                  w[a.ticker] = a.weight;
                });
                return <AllocationPieChart weights={w} />;
              })()}
            </div>
            {metrics.sector_allocation.length > 1 ||
            (metrics.sector_allocation.length === 1 &&
              metrics.sector_allocation[0].sector !== "Unknown") ? (
              <div className={styles.chartCard}>
                <h3>
                  Sector Allocation
                  <InfoTip text="How your portfolio is spread across industry sectors." />
                </h3>
                {(() => {
                  const w = {};
                  metrics.sector_allocation.forEach((s) => {
                    w[s.sector] = s.weight;
                  });
                  return <AllocationPieChart weights={w} />;
                })()}
              </div>
            ) : null}
          </div>
        </div>
      )}
      {metricsLoading && (
        <p className={styles.metricsHint}>Loading metrics...</p>
      )}
      {metricsError && <p className={styles.metricsHint}>{metricsError}</p>}

      <div className={styles.section}>
        <h2>Assets</h2>
        <AssetTable assets={portfolio.assets} onRemove={handleRemove} />
      </div>

      <div className={styles.addSection}>
        <h3>Add Asset</h3>
        <form className={styles.addForm} onSubmit={handleAddAsset}>
          <input
            type="text"
            placeholder="Ticker (e.g. AAPL)"
            value={ticker}
            onChange={(e) => setTicker(e.target.value)}
            required
          />
          <input
            type="text"
            placeholder="Name (e.g. Apple Inc.)"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <input
            type="number"
            placeholder="Shares (e.g. 50)"
            value={shares}
            onChange={(e) => setShares(e.target.value)}
          />
          <input
            type="number"
            step="0.001"
            placeholder="Exp. return (e.g. 0.10)"
            value={expReturn}
            onChange={(e) => setExpReturn(e.target.value)}
          />
          <input
            type="number"
            step="0.001"
            placeholder="Volatility (e.g. 0.20)"
            value={vol}
            onChange={(e) => setVol(e.target.value)}
          />
          <button type="submit" className={styles.addBtn}>
            Add
          </button>
        </form>
      </div>

      <div className={styles.section}>
        <h3>Or Upload CSV</h3>
        <CsvUpload onUpload={handleCsv} />
      </div>
    </div>
  );
}
