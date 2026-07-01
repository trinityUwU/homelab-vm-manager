// Modale de progression live d'une opération à job SSE (ex: suppression d'une VM)
// — accompagne l'attente au lieu de la laisser dans le vide.
import { AnimatePresence, motion } from "framer-motion";
import { EASE } from "./motion.js";

export default function ProgressDialog({ open, title, progress, message, done, success, onClose }) {
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="modal-overlay"
          onMouseDown={() => done && onClose()}
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
            <div className="progress-track">
              <motion.div
                className="progress-fill"
                initial={{ width: 0 }}
                animate={{ width: `${Math.round((progress || 0) * 100)}%` }}
                transition={{ duration: 0.4, ease: EASE }}
              />
            </div>
            <p className={`modal-step ${done ? (success ? "ok" : "err") : ""}`}>{message}</p>
            {done && (
              <div className="btn-row modal-actions">
                <button className="btn btn-primary" onClick={onClose}>Fermer</button>
              </div>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
