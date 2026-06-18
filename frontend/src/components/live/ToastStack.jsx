import { AnimatePresence, motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { useLive } from "./LiveContext.jsx";
import { StatusBadge, KindBadge } from "../HistoryBadges.jsx";

const ACCENT = {
  changed: "var(--online)", notified: "var(--essentielle)",
  error: "var(--danger)", ok: "var(--standard)", offline: "var(--text-muted)",
};

export default function ToastStack() {
  const { toasts, dismiss } = useLive();
  const navigate = useNavigate();

  const go = (toast, path) => { dismiss(toast.id); navigate(path); };

  return (
    <div className="toast-stack">
      <AnimatePresence>
        {toasts.map((t) => (
          <motion.div
            key={t.id}
            className="toast"
            style={{ "--toast-accent": ACCENT[t.status] || "var(--standard)" }}
            initial={{ opacity: 0, x: 60, scale: 0.92 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: 60, scale: 0.92, transition: { duration: 0.2 } }}
            transition={{ type: "spring", stiffness: 380, damping: 30 }}
            layout
          >
            <div className="toast-bar" />
            <div className="toast-body">
              <div className="toast-head">
                <span className="toast-title">{t.vm_name}</span>
                <button className="toast-x" onClick={() => dismiss(t.id)} aria-label="Fermer">×</button>
              </div>
              <div className="toast-badges"><KindBadge kind={t.kind} /><StatusBadge status={t.status} /></div>
              <div className="toast-msg">{t.reason_detail ? `${t.summary} — ${t.reason_detail}` : t.summary}</div>
              <div className="toast-actions">
                <button className="btn btn-ghost btn-xs" onClick={() => go(t, `/vm/${t.vm_id}`)}>La machine</button>
                <button className="btn btn-ghost btn-xs" onClick={() => go(t, `/maj?vm=${t.vm_id}`)}>Mises à jour</button>
              </div>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
