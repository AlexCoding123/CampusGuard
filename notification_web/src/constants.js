export const API_BASE = "http://backend:8080";

export const SEVERITY_CONFIG = {
  aggressive: {
    color: "#f0c400",
    bg: "rgba(240,196,0,0.10)",
    label: "AGGRESSIVE",
    glow: "0 0 18px rgba(240,196,0,0.4)",
  },
  critical: {
    color: "#ff2244",
    bg: "rgba(255,34,68,0.12)",
    label: "CRITICAL",
    glow: "0 0 18px rgba(255,34,68,0.6)",
  },
};

export function formatTime(ts) {
  try {
    return new Date(ts).toLocaleTimeString("en-US", {
      hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit",
    });
  } catch { return ts; }
}

export function formatDate(ts) {
  try {
    return new Date(ts).toLocaleDateString("en-US", {
      month: "short", day: "numeric", year: "numeric",
    });
  } catch { return ""; }
}
