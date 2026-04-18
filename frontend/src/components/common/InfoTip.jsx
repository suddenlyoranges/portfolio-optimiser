import { useState, useRef, useEffect } from "react";
import styles from "./InfoTip.module.css";

export default function InfoTip({ text }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    if (!open) return;
    const close = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [open]);

  return (
    <span className={styles.wrapper} ref={ref}>
      <button
        className={styles.icon}
        onClick={() => setOpen((v) => !v)}
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        aria-label="More info"
        type="button"
      >
        ?
      </button>
      {open && <span className={styles.bubble}>{text}</span>}
    </span>
  );
}
