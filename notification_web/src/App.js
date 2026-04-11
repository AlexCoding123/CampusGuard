import { useState, useEffect, useRef, useCallback } from "react";
import { API_BASE } from "./constants";
import FlashOverlay from "./components/FlashOverlay";
import AlertCard from "./components/AlertCard";
import Modal from "./components/Modal";
import Header from "./components/Header";
import Ticker from "./components/Ticker";
import StatusBar from "./components/StatusBar";

export default function App() {
  const [alerts, setAlerts]         = useState([]);
  const [connected, setConnected]   = useState(false);
  const [flashAlert, setFlashAlert] = useState(null);
  const [selected, setSelected]     = useState(null);
  const [newIds, setNewIds]         = useState(new Set());
  const [ticker, setTicker]         = useState("");

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
        setAlerts((prev) => [alert, ...prev]);
        setNewIds((prev) => { const s = new Set(prev); s.add(alert.id); return s; });
        setFlashAlert(alert);
        setTicker(`⚠ ${alert.threat_level} · ${alert.location}`);
        setTimeout(() => {
          setNewIds((prev) => { const s = new Set(prev); s.delete(alert.id); return s; });
        }, 4000);
      } catch (err) {
        console.error("Alert parse error:", err);
      }
    });

    es.addEventListener("heartbeat", () => { /* keep-alive, no-op */ });

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

  const handleTest = () => {
    fetch(`${API_BASE}/alerts/test`).catch(() => {});
  };

  return (
    <>
      {flashAlert && (
        <FlashOverlay alert={flashAlert} onDone={() => setFlashAlert(null)} />
      )}
      {selected && (
        <Modal alert={selected} onClose={() => setSelected(null)} />
      )}

      <div style={{ display: "flex", flexDirection: "column", height: "100%", height: "100dvh", overflow: "hidden" }}>
        <Header alertCount={alerts.length} connected={connected} onTest={handleTest} />
        <Ticker message={ticker} />

        {/* Alert feed */}
        <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: "12px", padding: "16px" }}>
          {alerts.length === 0 ? (
            <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: "16px", animation: "gridFade 0.6s ease", minHeight: "200px" }}>
              <div style={{ width: 72, height: 72, borderRadius: "50%", border: "1.5px solid #1e3a5a", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "1.8rem", color: "#1e3a5a" }}>
                👁
              </div>
              <div style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: "0.9rem", color: "#2a4a6a", letterSpacing: "0.2em", textTransform: "uppercase" }}>
                Awaiting threats…
              </div>
              <div style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: "0.72rem", color: "#1e3050", letterSpacing: "0.1em", textAlign: "center" }}>
                Tap TEST in the header to simulate an alert
              </div>
            </div>
          ) : (
            alerts.map((alert) => (
              <AlertCard key={alert.id} alert={alert} isNew={newIds.has(alert.id)} onClick={setSelected} />
            ))
          )}
        </div>

        <StatusBar alerts={alerts} />
      </div>
    </>
  );
}
