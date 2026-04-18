import { useState, useRef, useCallback } from "react";
import styles from "./CsvUpload.module.css";

export default function CsvUpload({ onUpload }) {
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef(null);

  const handleFile = (file) => {
    if (file && file.name.endsWith(".csv")) {
      onUpload(file);
    }
  };

  const downloadTemplate = useCallback(() => {
    const header = "ticker,name,shares,expected_return,volatility";
    const rows = [
      "AAPL,Apple Inc.,100,,",
      "MSFT,Microsoft Corp.,50,0.12,0.25",
      "GOOGL,Alphabet Inc.,30,,",
    ];
    const csv = [header, ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "portfolio_template.csv";
    a.click();
    URL.revokeObjectURL(url);
  }, []);

  const handleDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  return (
    <div
      className={`${styles.dropzone} ${dragActive ? styles.active : ""}`}
      onDragOver={(e) => {
        e.preventDefault();
        setDragActive(true);
      }}
      onDragLeave={() => setDragActive(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".csv"
        className={styles.input}
        onChange={(e) => handleFile(e.target.files[0])}
      />
      <p className={styles.text}>
        Drag &amp; drop a CSV file here, or <span>browse</span>
      </p>
      <p className={styles.hint}>
        Columns: ticker, name, shares, expected_return, volatility{" "}
        <button
          type="button"
          className={styles.templateBtn}
          onClick={(e) => {
            e.stopPropagation();
            downloadTemplate();
          }}
        >
          Download template
        </button>
      </p>
    </div>
  );
}
