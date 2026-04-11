export const API_BASE = "http://127.0.0.1:8000";

export const THREAT_CONFIG = {
  HIGH: {
    color: "#ff2244",
    bg: "rgba(255,34,68,0.12)",
    label: "HIGH",
    glow: "0 0 18px rgba(255,34,68,0.6)",
  },
  MEDIUM: {
    color: "#ff8c00",
    bg: "rgba(255,140,0,0.12)",
    label: "MED",
    glow: "0 0 18px rgba(255,140,0,0.5)",
  },
  LOW: {
    color: "#f0c400",
    bg: "rgba(240,196,0,0.10)",
    label: "LOW",
    glow: "0 0 18px rgba(240,196,0,0.4)",
  },
};

export function formatTime(ts) {
  try {
    return new Date(ts).toLocaleTimeString("en-US", {
      hour12: false,
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return ts;
  }
}

export function formatDate(ts) {
  try {
    return new Date(ts).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return "";
  }
}
