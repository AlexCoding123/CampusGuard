import { useEffect } from "react";
import { SEVERITY_CONFIG } from "../constants";

export default function FlashOverlay({ alert, onDone }) {
  const cfg = SEVERITY_CONFIG[alert?.severity] || SEVERITY_CONFIG.critical;

  useEffect(() => {
    const t = setTimeout(onDone, 2800);
    return () => clearTimeout(t);
  }, [onDone]);

  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 9999, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", background: `radial-gradient(ellipse at center, ${cfg.color}28 0%, #00000090 70%)`, animation: "flashIn 0.15s ease-out", pointerEvents: "none", padding: "20px" }}>
      <div style={{ position: "absolute", inset: 0, border: `3px solid ${cfg.color}`, animation: "borderPulse 0.6s ease-in-out 3", pointerEvents: "none" }} />
      <div style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: "clamp(1.3rem, 6vw, 2.4rem)", letterSpacing: "0.25em", color: cfg.color, textShadow: cfg.glow, animation: "textFlicker 0.3s ease-in-out", marginBottom: "0.6rem", textTransform: "uppercase", textAlign: "center", lineHeight: 1.2 }}>
        ⚠ {alert.severity?.toUpperCase()}<br/>THREAT DETECTED
      </div>
      <div style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: "clamp(0.75rem, 2.5vw, 1rem)", color: "#ffffff99", letterSpacing: "0.15em", textTransform: "uppercase", textAlign: "center" }}>
        {alert.location}
      </div>
    </div>
  );
}
