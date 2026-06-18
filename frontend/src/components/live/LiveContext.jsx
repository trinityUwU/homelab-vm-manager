import { createContext, useContext, useEffect, useRef, useState, useCallback } from "react";
import { openEventStream, api } from "../../api/client.js";

const LiveContext = createContext({ version: 0, lastEvent: null, toasts: [], dismiss: () => {} });

export const useLive = () => useContext(LiveContext);

// Un événement « notable » mérite une notification : une action terminée a eu un
// effet réel (resync de config, MAJ appliquée, MAJ à traiter, ou erreur). On ne
// notifie jamais l'état « en cours » — il est visible dans l'historique et le terminal.
function isNotable(e) {
  if (e.status === "running") return false;
  return e.reason === "config_change" || ["changed", "notified", "error"].includes(e.status);
}

const TOAST_TTL = 6500;
const MAX_TOASTS = 4;

export function LiveProvider({ children }) {
  const [version, setVersion] = useState(0);
  const [lastEvent, setLastEvent] = useState(null);
  const [toasts, setToasts] = useState([]);
  const notifyRef = useRef(true);

  const dismiss = useCallback((id) => setToasts((list) => list.filter((t) => t.id !== id)), []);

  const push = useCallback((event) => {
    const toast = { id: `${event.id}-${Date.now()}`, ...event };
    setToasts((list) => [toast, ...list].slice(0, MAX_TOASTS));
    setTimeout(() => dismiss(toast.id), TOAST_TTL);
  }, [dismiss]);

  // État courant du réglage notifications (rafraîchi quand les paramètres changent).
  useEffect(() => {
    api.getSettings().then((s) => { notifyRef.current = s.notifications_enabled !== false; });
    const onSettings = (e) => { notifyRef.current = e.detail?.notifications_enabled !== false; };
    window.addEventListener("settings-updated", onSettings);
    return () => window.removeEventListener("settings-updated", onSettings);
  }, []);

  // Flux temps réel : bump de version (les pages se rafraîchissent) + toast si notable.
  useEffect(() => {
    const es = openEventStream((event) => {
      setLastEvent(event);
      setVersion((v) => v + 1);
      if (notifyRef.current && isNotable(event)) push(event);
    });
    return () => es.close();
  }, [push]);

  return (
    <LiveContext.Provider value={{ version, lastEvent, toasts, dismiss }}>
      {children}
    </LiveContext.Provider>
  );
}
