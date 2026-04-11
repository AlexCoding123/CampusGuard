export default function Ticker({ message }) {
  return (
    <div style={{ height: "32px", background: "#030609", borderBottom: "1px solid #0f1e2e", overflow: "hidden", display: "flex", alignItems: "center", flexShrink: 0 }}>
      {message ? (
        <div key={message} style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: "0.8rem", letterSpacing: "0.15em", color: "#ff2244", whiteSpace: "nowrap", animation: "tickerSlide 6s linear forwards", paddingLeft: "100%" }}>
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
