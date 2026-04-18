export default function Loading({ message = "Loading..." }) {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        padding: "48px",
        color: "var(--color-text-muted)",
        fontSize: "0.84rem",
      }}
    >
      {message}
    </div>
  );
}
