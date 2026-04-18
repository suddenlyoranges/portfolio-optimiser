import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  listPortfolios,
  createPortfolio,
  deletePortfolio,
} from "../api/portfolios";
import PortfolioForm from "../components/portfolio/PortfolioForm";
import Loading from "../components/common/Loading";
import styles from "./dashboard.module.css";

export default function DashboardPage() {
  const [portfolios, setPortfolios] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const loadPortfolios = async () => {
    try {
      const res = await listPortfolios();
      setPortfolios(res.data);
    } catch {
      setError("Failed to load portfolios");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPortfolios();
  }, []);

  const handleCreate = async (data) => {
    try {
      await createPortfolio(data);
      setShowForm(false);
      loadPortfolios();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create portfolio");
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this portfolio?")) return;
    try {
      await deletePortfolio(id);
      loadPortfolios();
    } catch {
      setError("Failed to delete portfolio");
    }
  };

  if (loading) return <Loading />;

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1>Portfolios</h1>
        <button
          className={styles.createBtn}
          onClick={() => setShowForm(!showForm)}
        >
          {showForm ? "Cancel" : "+ New Portfolio"}
        </button>
      </div>

      {error && <div className={styles.error}>{error}</div>}

      {showForm && (
        <div className={styles.formCard}>
          <PortfolioForm
            onSubmit={handleCreate}
            onCancel={() => setShowForm(false)}
          />
        </div>
      )}

      {portfolios.length === 0 && !showForm ? (
        <div className={styles.emptyState}>
          <p>No portfolios yet. Create one to get started!</p>
        </div>
      ) : (
        <div className={styles.grid}>
          {portfolios.map((p) => (
            <div
              key={p.id}
              className={styles.card}
              onClick={() => navigate(`/portfolio/${p.id}`)}
            >
              <div className={styles.cardHeader}>
                <h3>{p.name}</h3>
                <button
                  className={styles.deleteBtn}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete(p.id);
                  }}
                >
                  ✕
                </button>
              </div>
              {p.description && <p className={styles.desc}>{p.description}</p>}
              <div className={styles.meta}>
                <span>
                  {p.asset_count} asset{p.asset_count !== 1 ? "s" : ""}
                </span>
                <span>{new Date(p.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
