import styles from "./AssetTable.module.css";

export default function AssetTable({ assets, onRemove }) {
  if (!assets || assets.length === 0) {
    return <p className={styles.empty}>No assets added yet.</p>;
  }

  return (
    <table className={styles.table}>
      <thead>
        <tr>
          <th>Ticker</th>
          <th>Name</th>
          <th>Shares</th>
          <th>Exp. Return</th>
          <th>Volatility</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {assets.map((a) => (
          <tr key={a.id}>
            <td className={styles.ticker}>{a.ticker}</td>
            <td>{a.name || "\u2014"}</td>
            <td>{a.shares != null ? a.shares : "\u2014"}</td>
            <td>
              {a.manual_expected_return != null
                ? `${(a.manual_expected_return * 100).toFixed(1)}%`
                : "Auto"}
            </td>
            <td>
              {a.manual_volatility != null
                ? `${(a.manual_volatility * 100).toFixed(1)}%`
                : "Auto"}
            </td>
            <td>
              <button
                className={styles.removeBtn}
                onClick={() => onRemove(a.id)}
              >
                ✕
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
