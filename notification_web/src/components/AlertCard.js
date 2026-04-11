import { THREAT_CONFIG, formatDate, formatTime } from "../constants";

export default function AlertCard({ alert, isNew, onClick }) {
  const cfg = THREAT_CONFIG[alert.threat_level] || THREAT_CONFIG.LOW;

  return (
    <div
      onClick={() => onClick(alert)}
      style={{
        background: "#0d1117",
        border: `1px solid ${isNew ? cfg.color : "#1e2a38"}`,
        borderLeft: `4px solid ${cfg.color}`,
        borderRadius: "6px",
        padding: "18px 20px",
        cursor: "pointer",
        transition: "border-color 0.4s, background 0.2s, box-shadow 0.3s",
        boxShadow: isNew ? cfg.glow : "none",
        animation: isNew ? "slideIn 0.3s cubic-bezier(0.22,1,0.36,1)" : "none",
        position: "relative",
        overflow: "hidden",
        /* Cards always take their natural height — feed scrolls, cards don't compress */
        flexShrink: 0,
        WebkitTapHighlightColor: "transparent",
        userSelect: "none",
      }}
      onMouseEnter={(e) => { e.currentTarget.style.background = "#111820"; }}
      onMouseLeave={(e) => { e.currentTarget.style.background = "#0d1117"; }}
    >
      {isNew && (
        <div style={{ position: "absolute", inset: 0, background: `linear-gradient(180deg, transparent 0%, ${cfg.color}18 50%, transparent 100%)`, animation: "scanLine 0.8s ease-out forwards", pointerEvents: "none" }} />
      )}

      {/* Top row */}
      <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "10px", flexWrap: "wrap" }}>
        <span style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: "0.85rem", fontWeight: 700, letterSpacing: "0.15em", color: cfg.color, background: cfg.bg, border: `1px solid ${cfg.color}55`, padding: "4px 10px", borderRadius: "3px", boxShadow: isNew ? cfg.glow : "none" }}>
          {cfg.label}
        </span>
        <span style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: "0.8rem", color: "#4a6a8a", letterSpacing: "0.04em" }}>
          {formatDate(alert.timestamp)} · {formatTime(alert.timestamp)}
        </span>
        {alert.video_url && (
          <span style={{ marginLeft: "auto", fontFamily: "'Share Tech Mono', monospace", fontSize: "0.78rem", color: "#2a8a6a", letterSpacing: "0.1em" }}>
            ▶ CLIP
          </span>
        )}
      </div>

      {/* Location */}
      <div style={{ fontFamily: "'Barlow Condensed', sans-serif", fontSize: "clamp(1rem, 3.5vw, 1.2rem)", fontWeight: 600, color: "#c8d8e8", letterSpacing: "0.06em", marginBottom: "6px", textTransform: "uppercase" }}>
        {alert.location}
      </div>

      {/* Description */}
      <div style={{ fontFamily: "'Barlow', sans-serif", fontSize: "clamp(0.88rem, 2.5vw, 0.95rem)", color: "#5a7a9a", lineHeight: 1.5 }}>
        {alert.description.length > 120 ? alert.description.slice(0, 117) + "…" : alert.description}
      </div>

      {/* Tap hint — readable colour, not just a ghost */}
      <div style={{ marginTop: "12px", fontFamily: "'Share Tech Mono', monospace", fontSize: "0.68rem", color: "#3a6a8a", letterSpacing: "0.12em" }}>
        TAP FOR DETAILS →
      </div>
    </div>
  );
}
