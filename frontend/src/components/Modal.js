import { useEffect, useRef, useCallback } from "react";
import { SEVERITY_CONFIG, formatDate, formatTime } from "../constants";
import useIsMobile from "../hooks/useIsMobile";

export default function Modal({ group, onClose }) {
  const cfg = SEVERITY_CONFIG[group.severity] || SEVERITY_CONFIG.aggressive;
  const isMobile = useIsMobile();
  const latest = group.alerts[0];
  const videos = group.alerts.filter(a => a.video_url);

  const sheetRef  = useRef(null);
  const startY    = useRef(0);
  const currentY  = useRef(0);
  const dragging  = useRef(false);

  const onTouchStart = useCallback((e) => {
    if (sheetRef.current && sheetRef.current.scrollTop > 0) return;
    startY.current = e.touches[0].clientY;
    dragging.current = true;
  }, []);

  const onTouchMove = useCallback((e) => {
    if (!dragging.current) return;
    currentY.current = e.touches[0].clientY;
    const delta = currentY.current - startY.current;
    if (delta > 0 && sheetRef.current) {
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
        sheetRef.current.style.transition = "transform 0.25s ease";
        sheetRef.current.style.transform = "translateY(100%)";
        setTimeout(onClose, 250);
      } else {
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
      style={{ position: "fixed", inset: 0, zIndex: 1000, background: "rgba(0,4,10,0.88)", display: "flex", alignItems: isMobile ? "flex-end" : "center", justifyContent: "center", backdropFilter: "blur(4px)", animation: "fadeIn 0.2s ease" }}
    >
      <div
        ref={sheetRef}
        onClick={(e) => e.stopPropagation()}
        onTouchStart={isMobile ? onTouchStart : undefined}
        onTouchMove={isMobile ? onTouchMove : undefined}
        onTouchEnd={isMobile ? onTouchEnd : undefined}
        style={{ background: "#080e16", border: `1px solid ${cfg.color}55`, borderTop: `3px solid ${cfg.color}`, borderRadius: isMobile ? "16px 16px 0 0" : "8px", width: "100%", maxWidth: isMobile ? "100%" : "680px", maxHeight: isMobile ? "100dvh" : "98vh", overflowY: "auto", boxShadow: `0 0 60px ${cfg.color}22, 0 0 0 1px #1a2a3a`, animation: isMobile ? "sheetIn 0.3s cubic-bezier(0.22,1,0.36,1)" : "modalIn 0.25s cubic-bezier(0.22,1,0.36,1)", paddingBottom: "env(safe-area-inset-bottom, 0px)" }}
      >
        {/* Drag handle */}
        {isMobile && (
          <div style={{ display: "flex", justifyContent: "center", padding: "12px 0 4px" }}>
            <div style={{ width: 44, height: 5, borderRadius: 3, background: "#2a4a6a" }} />
          </div>
        )}

        {/* Header */}
        <div style={{ display: "flex", alignItems: "flex-start", gap: "12px", padding: "16px 20px", borderBottom: "1px solid #1a2a3a", background: `linear-gradient(90deg, ${cfg.color}0a, transparent)` }}>
          <div style={{ display: "flex", flexDirection: "column", gap: "6px", flexShrink: 0, marginTop: "2px" }}>
            <span style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: "0.82rem", fontWeight: 700, letterSpacing: "0.12em", color: cfg.color, background: cfg.bg, border: `1px solid ${cfg.color}55`, padding: "5px 12px", borderRadius: "3px", boxShadow: cfg.glow, whiteSpace: "nowrap" }}>
              {cfg.label}
            </span>
            <span style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: "0.7rem", color: "#3a6a8a", background: "#0a1520", border: "1px solid #1e3a5a", padding: "3px 10px", borderRadius: "3px", textAlign: "center" }}>
              GROUP #{group.group_id}
            </span>
          </div>
          <span style={{ fontFamily: "'Barlow Condensed', sans-serif", fontSize: "clamp(1rem, 3vw, 1.2rem)", fontWeight: 600, color: "#c8d8e8", letterSpacing: "0.08em", textTransform: "uppercase", flex: 1, lineHeight: 1.3, wordBreak: "break-word" }}>
            {latest.location}
          </span>
          <button onClick={onClose} style={{ background: "none", border: "none", color: "#4a6a8a", cursor: "pointer", fontSize: "1.4rem", lineHeight: 1, padding: "0", minWidth: "44px", minHeight: "44px", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
            ✕
          </button>
        </div>

        <div style={{ padding: "20px" }}>

          {/* Videos — top, grouped */}
          {videos.length > 0 ? (
            <div style={{ marginBottom: "18px" }}>
              <div style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: "0.65rem", color: "#3a5a7a", letterSpacing: "0.15em", marginBottom: "12px" }}>
                INCIDENT FOOTAGE {videos.length > 1 ? `(${videos.length} CLIPS)` : ""}
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                {videos.map((a, i) => (
                  <div key={i}>
                    {videos.length > 1 && (
                      <div style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: "0.62rem", color: "#2a8a6a", letterSpacing: "0.1em", marginBottom: "6px" }}>
                        CLIP {i + 1} · {formatTime(a.timestamp)}
                      </div>
                    )}
                    <video src={a.video_url} controls playsInline style={{ width: "100%", minHeight: "260px", borderRadius: "4px", border: `1px solid ${cfg.color}33`, background: "#000", boxShadow: `0 0 20px ${cfg.color}22`, display: "block" }} />
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div style={{ textAlign: "center", padding: "28px 24px", background: "#0a1018", border: "1px dashed #1e2e3e", borderRadius: "4px", fontFamily: "'Share Tech Mono', monospace", fontSize: "0.78rem", color: "#2a4a6a", letterSpacing: "0.1em", marginBottom: "18px" }}>
              NO FOOTAGE AVAILABLE
            </div>
          )}

          {/* Meta grid — only show for single-event groups */}
          {group.alerts.length === 1 && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginBottom: "18px" }}>
              {[
                ["TIMESTAMP", `${formatDate(latest.timestamp)} ${formatTime(latest.timestamp)}`],
                ["CONFIDENCE", `${Math.round(latest.confidence * 100)}%`],
                ["LOCATION", latest.location],
              ].map(([label, val]) => (
                <div key={label} style={{ background: "#0d1520", border: "1px solid #1a2a3a", borderRadius: "4px", padding: "12px 14px" }}>
                  <div style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: "0.65rem", color: "#3a5a7a", letterSpacing: "0.15em", marginBottom: "5px" }}>{label}</div>
                  <div style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: "0.82rem", color: "#8aaac8", wordBreak: "break-all" }}>{val}</div>
                </div>
              ))}
            </div>
          )}

          {/* Event timeline if multiple */}
          {group.alerts.length > 1 && (
            <div style={{ background: "#0d1520", border: "1px solid #1a2a3a", borderRadius: "4px", padding: "16px", marginBottom: "18px" }}>
              <div style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: "0.65rem", color: "#3a5a7a", letterSpacing: "0.15em", marginBottom: "12px" }}>EVENT TIMELINE</div>
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                {group.alerts.map((a, i) => (
                  <div key={i} style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <div style={{ width: 6, height: 6, borderRadius: "50%", background: cfg.color, flexShrink: 0 }} />
                    <span style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: "0.72rem", color: "#5a7a9a" }}>
                      {formatTime(a.timestamp)} — {Math.round(a.confidence * 100)}% confidence
                      {a.video_url && <span style={{ color: "#2a8a6a" }}> · clip {i + 1}</span>}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Reports */}
          {group.alerts.length === 1 ? (
            // Single alert — show one report block if available
            latest.report ? (
              <div style={{ background: "#0d1520", border: "1px solid #1a2a3a", borderRadius: "4px", padding: "16px" }}>
                <div style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: "0.65rem", color: "#3a5a7a", letterSpacing: "0.15em", marginBottom: "10px" }}>REPORT</div>
                <div style={{ fontFamily: "'Barlow', sans-serif", fontSize: "clamp(0.92rem, 2.5vw, 1rem)", color: "#a0bcd4", lineHeight: 1.65 }}>{latest.report}</div>
              </div>
            ) : null
          ) : (
            // Multiple alerts — show each report labeled by clip number
            group.alerts.some(a => a.report) && (
              <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                {group.alerts.map((a, i) => a.report ? (
                  <div key={i} style={{ background: "#0d1520", border: "1px solid #1a2a3a", borderRadius: "4px", padding: "16px" }}>
                    <div style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: "0.65rem", color: "#3a5a7a", letterSpacing: "0.15em", marginBottom: "10px" }}>
                      REPORT · CLIP {i + 1} · {formatTime(a.timestamp)}
                    </div>
                    <div style={{ fontFamily: "'Barlow', sans-serif", fontSize: "clamp(0.92rem, 2.5vw, 1rem)", color: "#a0bcd4", lineHeight: 1.65 }}>{a.report}</div>
                  </div>
                ) : null)}
              </div>
            )
          )}
        </div>
      </div>
    </div>
  );
}
