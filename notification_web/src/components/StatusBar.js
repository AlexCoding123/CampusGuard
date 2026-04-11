import { THREAT_CONFIG, API_BASE } from "../constants";

export default function StatusBar({ alerts }) {
  const isMobile = window.innerWidth < 640;

  return (
    <footer
      style={{
        display: "flex",
        alignItems: "center",
        gap: isMobile ? "16px" : "28px",
        padding: isMobile ? "10px 20px" : "14px 24px",
        paddingBottom: "max(" + (isMobile ? "10px" : "14px") + ", env(safe-area-inset-bottom, " + (isMobile ? "10px" : "14px") + "))",
        borderTop: "1px solid #0f1e2e",
        background: "#030609",
        flexShrink: 0,
      }}
    >
      {["HIGH", "MEDIUM", "LOW"].map((level) => {
        const cfg = THREAT_CONFIG[level];
        const count = alerts.filter((a) => a.threat_level === level).length;
        return (
          <div key={level} style={{ display: "flex", alignItems: "center", gap: isMobile ? "7px" : "9px" }}>
            <div style={{
              width: isMobile ? 8 : 11,
              height: isMobile ? 8 : 11,
              borderRadius: "50%",
              background: cfg.color,
              boxShadow: cfg.glow,
              flexShrink: 0,
            }} />
            <span style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: isMobile ? "0.72rem" : "0.85rem", color: "#2a4a6a", letterSpacing: "0.08em" }}>
              {cfg.label}
            </span>
            <span style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: isMobile ? "0.82rem" : "1rem", color: cfg.color, fontWeight: 700 }}>
              {count}
            </span>
          </div>
        );
      })}

      <div style={{ marginLeft: "auto", fontFamily: "'Share Tech Mono', monospace", fontSize: isMobile ? "0.6rem" : "0.72rem", color: "#1e3050", letterSpacing: "0.06em", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: "38vw" }}>
        {API_BASE}/alerts/stream
      </div>
    </footer>
  );
}
