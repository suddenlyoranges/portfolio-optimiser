import styles from "./Footer.module.css";

export default function Footer() {
  return (
    <div className={styles.footer}>
      Disclaimer: This is a demonstration portfolio optimization tool. All data
      is simulated or uses publicly available information. This tool is for
      educational purposes only and should not be considered financial advice.
      Always consult with a qualified financial advisor before making investment
      decisions. Guest mode: Your data is stored locally and will not persist
      across sessions or devices.
    </div>
  );
}
