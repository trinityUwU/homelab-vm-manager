// Confirmation custom (remplace window.confirm), cohérente avec le design system.
import { AnimatePresence, motion } from "framer-motion";
import { EASE } from "./motion.js";

export default function ConfirmDialog({
  open, title, message, confirmLabel = "Confirmer", cancelLabel = "Annuler",
  danger = false, onConfirm, onCancel,
}) {
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="modal-overlay"
          onMouseDown={onCancel}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0, transition: { duration: 0.15 } }}
        >
          <motion.div
            className="modal-panel"
            onMouseDown={(e) => e.stopPropagation()}
            initial={{ opacity: 0, y: 12, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.97, transition: { duration: 0.15 } }}
            transition={{ duration: 0.22, ease: EASE }}
          >
            <div className="modal-title">{title}</div>
            <p className="modal-msg">{message}</p>
            <div className="btn-row modal-actions">
              <button className="btn btn-ghost" onClick={onCancel}>{cancelLabel}</button>
              <button className={`btn ${danger ? "btn-danger" : "btn-primary"}`} onClick={onConfirm}>
                {confirmLabel}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
