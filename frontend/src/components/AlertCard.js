import { SEVERITY_CONFIG, formatDate, formatTime } from "../constants";

// A single video entry within a group card
function VideoEntry({ url, index }) {
  return (
    <div style={{ marginTop: index > 0 ? "8px" : "0" }}>
      {index > 0 && (
        <div style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: "0.62rem", color: "#2a8a6a", letterSpacing: "0.1em", marginBottom: "4px" }}>
          ▶ CLIP {index + 1}
        </div>
      )}
    </div>
  );
}

export default function AlertCard({ group, isNew, onClick }) {
  const cfg = SEVERITY_CONFIG[group.severity] || SEVERITY_CONFIG.aggressive;
  const latest = group.alerts[0];
  const videoCount = group.alerts.filter(a => a.video_url).length;

  return (
    <div
      onClick={() => onClick(group)}
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

        {/* Group ID badge */}
        <span style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: "0.72rem", color: "#4a6a8a", background: "#0a1520", border: "1px solid #1e3a5a", padding: "3px 8px", borderRadius: "3px" }}>
          GROUP #{group.group_id}
        </span>

        <span style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: "0.78rem", color: "#4a6a8a", letterSpacing: "0.04em" }}>
          {formatDate(latest.timestamp)} · {formatTime(latest.timestamp)}
        </span>

        {videoCount > 0 && (
          <span style={{ marginLeft: "auto", fontFamily: "'Share Tech Mono', monospace", fontSize: "0.78rem", color: "#2a8a6a", letterSpacing: "0.1em" }}>
            ▶ {videoCount} CLIP{videoCount > 1 ? "S" : ""}
          </span>
        )}
      </div>

      {/* Location */}
      <div style={{ fontFamily: "'Barlow Condensed', sans-serif", fontSize: "clamp(1rem, 3.5vw, 1.2rem)", fontWeight: 600, color: "#c8d8e8", letterSpacing: "0.06em", marginBottom: "6px", textTransform: "uppercase" }}>
        {latest.location}
      </div>

      {/* Confidence + alert count */}
      <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
        <div style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: "0.78rem", color: "#5a7a9a" }}>
          CONFIDENCE: <span style={{ color: cfg.color }}>{Math.round(latest.confidence * 100)}%</span>
        </div>
        {group.alerts.length > 1 && (
          <div style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: "0.72rem", color: "#3a6a8a", background: "#0a1520", border: "1px solid #1e3a5a", padding: "2px 8px", borderRadius: "3px" }}>
            {group.alerts.length} EVENTS
          </div>
        )}
      </div>

      {/* Tap hint */}
      <div style={{ marginTop: "12px", fontFamily: "'Share Tech Mono', monospace", fontSize: "0.68rem", color: "#3a6a8a", letterSpacing: "0.12em" }}>
        TAP FOR DETAILS →
      </div>
    </div>
  );
}
