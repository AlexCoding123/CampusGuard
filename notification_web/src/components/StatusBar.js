import { SEVERITY_CONFIG } from "../constants";
import useIsMobile from "../hooks/useIsMobile";

export default function StatusBar({ groups }) {
  const isMobile = useIsMobile();
  const allAlerts = Array.from(groups.values()).flatMap(g => g.alerts);

  return (
    <footer style={{
      display: "flex", alignItems: "center",
      gap: isMobile ? "12px" : "28px",
      padding: isMobile ? "8px 16px" : "14px 24px",
      paddingBottom: `max(${isMobile ? "8px" : "14px"}, env(safe-area-inset-bottom, ${isMobile ? "8px" : "14px"}))`,
      borderTop: "1px solid #0f1e2e",
      background: "#030609",
      flexShrink: 0,
    }}>
      {["aggressive", "critical"].map((level) => {
        const cfg = SEVERITY_CONFIG[level];
        const count = allAlerts.filter((a) => a.severity === level).length;
        return (
          <div key={level} style={{ display: "flex", alignItems: "center", gap: isMobile ? "5px" : "9px" }}>
            <div style={{ width: isMobile ? 6 : 11, height: isMobile ? 6 : 11, borderRadius: "50%", background: cfg.color, boxShadow: cfg.glow, flexShrink: 0 }} />
            <span style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: isMobile ? "0.6rem" : "0.85rem", color: "#2a4a6a", letterSpacing: "0.06em" }}>{cfg.label}</span>
            <span style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: isMobile ? "0.68rem" : "1rem", color: cfg.color, fontWeight: 700 }}>{count}</span>
          </div>
        );
      })}
    </footer>
  );
}
