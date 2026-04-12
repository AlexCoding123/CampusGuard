export default function Header({ alertCount, connected }) {
  return (
    <header
      style={{
        display: "flex",
        alignItems: "center",
        gap: "12px",
        padding: "14px 16px",
        paddingTop: "max(14px, env(safe-area-inset-top, 14px))",
        borderBottom: "1px solid #0f1e2e",
        background: "linear-gradient(180deg, #07111c, #050b14)",
        flexShrink: 0,
      }}
    >
      {/* Logo */}
      <div style={{ position: "relative", width: 36, height: 36, flexShrink: 0 }}>
        <div style={{ position: "absolute", inset: 0, border: "2px solid #ff2244", borderRadius: "50%", animation: "borderPulse 2s ease-in-out infinite" }} />
        <div style={{ position: "absolute", inset: 6, background: "#ff2244", borderRadius: "50%" }} />
      </div>

      {/* Brand */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontFamily: "'Barlow Condensed', sans-serif", fontWeight: 700, fontSize: "clamp(1.1rem, 3.5vw, 1.5rem)", letterSpacing: "0.2em", color: "#e8f0f8", textTransform: "uppercase", whiteSpace: "nowrap" }}>
          CampusGuard
        </div>
        <div style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: "clamp(0.58rem, 1.6vw, 0.72rem)", color: "#3a5a7a", letterSpacing: "0.07em", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
          THREAT DETECTION · v1.0
        </div>
      </div>

      {/* Right controls */}
      <div style={{ display: "flex", alignItems: "center", gap: "16px", flexShrink: 0 }}>
        {/* Counter */}
        <div style={{ textAlign: "right" }}>
          <div style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: "clamp(1.4rem, 4.5vw, 1.9rem)", fontWeight: 700, color: alertCount > 0 ? "#ff2244" : "#2a4a6a", lineHeight: 1, textShadow: alertCount > 0 ? "0 0 16px rgba(255,34,68,0.55)" : "none" }}>
            {String(alertCount).padStart(3, "0")}
          </div>
          <div style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: "0.6rem", color: "#3a5a7a", letterSpacing: "0.1em" }}>ALERTS</div>
        </div>

        {/* Connection dot */}
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "4px" }}>
          <div style={{ width: 11, height: 11, borderRadius: "50%", background: connected ? "#00ff88" : "#ff2244", boxShadow: connected ? "0 0 10px #00ff88" : "0 0 10px #ff2244", animation: "blink 1.8s ease-in-out infinite" }} />
          <span style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: "0.56rem", color: connected ? "#00ff88" : "#ff2244", letterSpacing: "0.06em" }}>
            {connected ? "LIVE" : "RETRY"}
          </span>
        </div>
      </div>
    </header>
  );
}
