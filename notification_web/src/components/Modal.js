import { useEffect, useRef, useCallback } from "react";
import { THREAT_CONFIG, formatDate, formatTime } from "../constants";

export default function Modal({ alert, onClose }) {
  const cfg = THREAT_CONFIG[alert.threat_level] || THREAT_CONFIG.LOW;
  const isMobile = window.innerWidth < 640;

  /* ── swipe-to-dismiss (mobile only) ─────────────────────── */
  const sheetRef   = useRef(null);
  const startY     = useRef(0);
  const currentY   = useRef(0);
  const dragging   = useRef(false);

  const onTouchStart = useCallback((e) => {
    // Only allow drag when sheet is scrolled to the top
    if (sheetRef.current && sheetRef.current.scrollTop > 0) return;
    startY.current = e.touches[0].clientY;
    dragging.current = true;
  }, []);

  const onTouchMove = useCallback((e) => {
    if (!dragging.current) return;
    currentY.current = e.touches[0].clientY;
    const delta = currentY.current - startY.current;
    if (delta > 0 && sheetRef.current) {
      // Translate sheet down as finger drags
      sheetRef.current.style.transform = `translateY(${delta}px)`;
      sheetRef.current.style.transition = "none";
    }
  }, []);

  const onTouchEnd = useCallback(() => {
    if (!dragging.current) return;
    dragging.current = false;
    const delta = currentY.current - startY.current;
    if (sheetRef.current) {
      if (delta > 120) {
        // Flick — animate off screen then close
        sheetRef.current.style.transition = "transform 0.25s ease";
        sheetRef.current.style.transform = "translateY(100%)";
        setTimeout(onClose, 250);
      } else {
        // Snap back
        sheetRef.current.style.transition = "transform 0.2s ease";
        sheetRef.current.style.transform = "translateY(0)";
      }
    }
  }, [onClose]);

  useEffect(() => {
    const handler = (e) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handler);
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", handler);
      document.body.style.overflow = "";
    };
  }, [onClose]);

  return (
    <div
      onClick={onClose}
      style={{
        position: "fixed", inset: 0, zIndex: 1000,
        background: "rgba(0,4,10,0.88)",
        display: "flex",
        alignItems: isMobile ? "flex-end" : "center",
        justifyContent: "center",
        backdropFilter: "blur(4px)",
        animation: "fadeIn 0.2s ease",
      }}
    >
      <div
        ref={sheetRef}
        onClick={(e) => e.stopPropagation()}
        onTouchStart={isMobile ? onTouchStart : undefined}
        onTouchMove={isMobile ? onTouchMove : undefined}
        onTouchEnd={isMobile ? onTouchEnd : undefined}
        style={{
          background: "#080e16",
          border: `1px solid ${cfg.color}55`,
          borderTop: `3px solid ${cfg.color}`,
          borderRadius: isMobile ? "16px 16px 0 0" : "8px",
          width: "100%",
          maxWidth: isMobile ? "100%" : "680px",
          maxHeight: isMobile ? "92dvh" : "88vh",
          overflowY: "auto",
          boxShadow: `0 0 60px ${cfg.color}22, 0 0 0 1px #1a2a3a`,
          animation: isMobile ? "sheetIn 0.3s cubic-bezier(0.22,1,0.36,1)" : "modalIn 0.25s cubic-bezier(0.22,1,0.36,1)",
          paddingBottom: "env(safe-area-inset-bottom, 0px)",
        }}
      >
        {/* Drag handle */}
        {isMobile && (
          <div style={{ display: "flex", justifyContent: "center", padding: "12px 0 4px" }}>
            <div style={{ width: 44, height: 5, borderRadius: 3, background: "#2a4a6a" }} />
          </div>
        )}

        {/* Header — location wraps instead of truncating */}
        <div style={{ display: "flex", alignItems: "flex-start", gap: "12px", padding: "16px 20px", borderBottom: "1px solid #1a2a3a", background: `linear-gradient(90deg, ${cfg.color}0a, transparent)` }}>
          <span style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: "0.82rem", fontWeight: 700, letterSpacing: "0.12em", color: cfg.color, background: cfg.bg, border: `1px solid ${cfg.color}55`, padding: "5px 12px", borderRadius: "3px", boxShadow: cfg.glow, whiteSpace: "nowrap", flexShrink: 0, marginTop: "2px" }}>
            {cfg.label}
          </span>
          {/* flex:1 + normal white-space = text wraps fully, no ellipsis */}
          <span style={{ fontFamily: "'Barlow Condensed', sans-serif", fontSize: "clamp(1rem, 3vw, 1.2rem)", fontWeight: 600, color: "#c8d8e8", letterSpacing: "0.08em", textTransform: "uppercase", flex: 1, lineHeight: 1.3, wordBreak: "break-word" }}>
            {alert.location}
          </span>
          <button
            onClick={onClose}
            style={{ background: "none", border: "none", color: "#4a6a8a", cursor: "pointer", fontSize: "1.4rem", lineHeight: 1, padding: "0", minWidth: "44px", minHeight: "44px", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div style={{ padding: "20px" }}>
          {/* Meta grid */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginBottom: "18px" }}>
            {[
              ["ALERT ID", alert.id],
              ["TIMESTAMP", `${formatDate(alert.timestamp)} ${formatTime(alert.timestamp)}`],
              ...(alert.lat && alert.lng ? [["COORDINATES", `${parseFloat(alert.lat).toFixed(4)}, ${parseFloat(alert.lng).toFixed(4)}`]] : []),
            ].map(([label, val]) => (
              <div key={label} style={{ background: "#0d1520", border: "1px solid #1a2a3a", borderRadius: "4px", padding: "12px 14px" }}>
                <div style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: "0.65rem", color: "#3a5a7a", letterSpacing: "0.15em", marginBottom: "5px" }}>{label}</div>
                <div style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: "0.82rem", color: "#8aaac8", wordBreak: "break-all" }}>{val}</div>
              </div>
            ))}
          </div>

          {/* Description */}
          <div style={{ background: "#0d1520", border: "1px solid #1a2a3a", borderRadius: "4px", padding: "16px", marginBottom: "18px" }}>
            <div style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: "0.65rem", color: "#3a5a7a", letterSpacing: "0.15em", marginBottom: "10px" }}>THREAT ASSESSMENT</div>
            <div style={{ fontFamily: "'Barlow', sans-serif", fontSize: "clamp(0.92rem, 2.5vw, 1rem)", color: "#a0bcd4", lineHeight: 1.65 }}>{alert.description}</div>
          </div>

          {/* Video */}
          {alert.video_url ? (
            <div>
              <div style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: "0.65rem", color: "#3a5a7a", letterSpacing: "0.15em", marginBottom: "10px" }}>INCIDENT FOOTAGE</div>
              <video src={alert.video_url} controls playsInline style={{ width: "100%", borderRadius: "4px", border: `1px solid ${cfg.color}33`, background: "#000", boxShadow: `0 0 20px ${cfg.color}22` }} />
            </div>
          ) : (
            <div style={{ textAlign: "center", padding: "28px 24px", background: "#0a1018", border: "1px dashed #1e2e3e", borderRadius: "4px", fontFamily: "'Share Tech Mono', monospace", fontSize: "0.78rem", color: "#2a4a6a", letterSpacing: "0.1em" }}>
              NO FOOTAGE AVAILABLE
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
