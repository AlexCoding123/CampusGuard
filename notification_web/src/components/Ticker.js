export default function Ticker({ message, tickerKey }) {
  return (
    <div style={{ height: "32px", background: "#030609", borderBottom: "1px solid #0f1e2e", overflow: "hidden", display: "flex", alignItems: "center", flexShrink: 0 }}>
      {message && tickerKey ? (
        <div
          key={tickerKey}
          style={{
            fontFamily: "'Share Tech Mono', monospace",
            fontSize: "0.8rem",
            letterSpacing: "0.15em",
            color: "#ff2244",
            whiteSpace: "nowrap",
            paddingLeft: "100%",
            display: "inline-block",
            animation: "tickerSlide 14s linear",
          }}
        >
          {message}
        </div>
      ) : (
        <div style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: "0.72rem", letterSpacing: "0.1em", color: "#1e3a5a", paddingLeft: "20px" }}>
          MONITORING ACTIVE — NO RECENT EVENTS
        </div>
      )}
    </div>
  );
}
