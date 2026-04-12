import { useState, useEffect, useRef, useCallback } from "react";
import { API_BASE } from "./constants";
import { playAlarm, unlockAudio } from "./utils/alarm";
import FlashOverlay from "./components/FlashOverlay";
import AlertCard from "./components/AlertCard";
import Modal from "./components/Modal";
import Header from "./components/Header";
import Ticker from "./components/Ticker";
import StatusBar from "./components/StatusBar";

// Groups is a Map: group_id -> { group_id, severity, alerts: [...] }
function addAlertToGroups(groups, alert) {
  const next = new Map(groups);
  const existing = next.get(alert.group_id);
  if (existing) {
    next.set(alert.group_id, {
      ...existing,
      severity: alert.severity, // update to latest
      alerts: [alert, ...existing.alerts],
    });
  } else {
    next.set(alert.group_id, {
      group_id: alert.group_id,
      severity: alert.severity,
      alerts: [alert],
    });
  }
  return next;
}

export default function App() {
  const [groups, setGroups]           = useState(new Map());
  const [groupOrder, setGroupOrder]   = useState([]); // group_ids in arrival order
  const [connected, setConnected]     = useState(false);
  const [flashAlert, setFlashAlert]   = useState(null);
  const [selected, setSelected]       = useState(null);
  const [newIds, setNewIds]           = useState(new Set());
  const [ticker, setTicker]           = useState({ text: "", key: 0 });
  const [audioReady, setAudioReady]   = useState(false);

  const esRef    = useRef(null);
  const retryRef = useRef(null);

  const connect = useCallback(() => {
    if (esRef.current) esRef.current.close();
    const es = new EventSource(`${API_BASE}/alerts/stream`);
    esRef.current = es;
    es.onopen = () => setConnected(true);

    es.addEventListener("threat", (e) => {
      try {
        const alert = JSON.parse(e.data);

        // Check if this group already exists before updating state
        setGroups((prev) => {
          const isNewGroup = !prev.has(alert.group_id);

          if (isNewGroup) {
            // First event in this group — play sound + show flash + ticker
            playAlarm();
            setFlashAlert(alert);
            setTicker({ text: `⚠ ${alert.severity.toUpperCase()} · ${alert.location}`, key: `${alert.group_id}-${alert.timestamp}` });
            setNewIds((s) => { const n = new Set(s); n.add(alert.group_id); return n; });
            setTimeout(() => {
              setNewIds((s) => { const n = new Set(s); n.delete(alert.group_id); return n; });
            }, 4000);
            setGroupOrder((prev) => [alert.group_id, ...prev]);
          }
          // Always merge the alert into the group silently if it already exists
          return addAlertToGroups(prev, alert);
        });

        // If this group is currently open in the modal, refresh it
        setSelected((prev) => {
          if (prev && prev.group_id === alert.group_id) {
            return addAlertToGroups(new Map([[alert.group_id, prev]]), alert).get(alert.group_id);
          }
          return prev;
        });
      } catch (err) {
        console.error("Alert parse error:", err);
      }
    });

    es.addEventListener("heartbeat", () => {});
    es.addEventListener("reset", () => {
      setGroups(new Map());
      setGroupOrder([]);
    });
    es.onerror = () => {
      setConnected(false);
      es.close();
      retryRef.current = setTimeout(connect, 3000);
    };
  }, []);

  useEffect(() => {
    connect();
    return () => {
      if (esRef.current) esRef.current.close();
      if (retryRef.current) clearTimeout(retryRef.current);
    };
  }, [connect]);

  const handleActivate = () => {
    unlockAudio();
    setAudioReady(true);
  };

  const totalAlerts = Array.from(groups.values()).reduce((sum, g) => sum + g.alerts.length, 0);

  return (
    <>
      {flashAlert && <FlashOverlay alert={flashAlert} onDone={() => setFlashAlert(null)} />}
      {selected && <Modal group={selected} onClose={() => setSelected(null)} />}

      {!audioReady && (
        <div
          onClick={handleActivate}
          style={{ position: "fixed", top: 0, left: 0, right: 0, zIndex: 8000, background: "#ff2244", padding: "10px 20px", display: "flex", alignItems: "center", justifyContent: "center", gap: "10px", cursor: "pointer" }}
        >
          <span style={{ fontSize: "1rem" }}>🔊</span>
          <span style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: "0.8rem", color: "#fff", letterSpacing: "0.15em" }}>
            TAP HERE TO ACTIVATE AUDIO ALERTS
          </span>
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", height: "100dvh", overflow: "hidden", paddingTop: audioReady ? 0 : "40px", transition: "padding-top 0.3s ease" }}>
        <Header alertCount={totalAlerts} connected={connected} />
        <Ticker message={ticker.text} tickerKey={ticker.key} />

        <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: "12px", padding: "16px" }}>
          {groupOrder.length === 0 ? (
            <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: "16px", animation: "gridFade 0.6s ease", minHeight: "200px" }}>
              <div style={{ width: 72, height: 72, borderRadius: "50%", border: "1.5px solid #1e3a5a", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "1.8rem", color: "#1e3a5a" }}>
                👁
              </div>
              <div style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: "0.9rem", color: "#2a4a6a", letterSpacing: "0.2em", textTransform: "uppercase" }}>
                Awaiting threats…
              </div>
              <div style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: "0.72rem", color: "#1e3050", letterSpacing: "0.1em", textAlign: "center" }}>
                {audioReady ? "Monitoring active" : "Tap the banner above to enable sound"}
              </div>
            </div>
          ) : (
            groupOrder.map((gid) => {
              const group = groups.get(gid);
              if (!group) return null;
              return (
                <AlertCard
                  key={gid}
                  group={group}
                  isNew={newIds.has(gid)}
                  onClick={setSelected}
                />
              );
            })
          )}
        </div>

        <StatusBar groups={groups} />
      </div>
    </>
  );
}
