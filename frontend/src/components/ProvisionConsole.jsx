// Terminal live + barre de progression du provisioning, alimentés par le WebSocket.
import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { EASE } from "./motion.js";

export default function ProvisionConsole({ lines, progress }) {
  const endRef = useRef(null);
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [lines]);

  return (
    <div>
      <div className="progress-track">
        <motion.div
          className="progress-fill"
          initial={{ width: 0 }}
          animate={{ width: `${Math.round((progress || 0) * 100)}%` }}
          transition={{ duration: 0.4, ease: EASE }}
        />
      </div>
      <div className="terminal">
        {lines.map((l, i) => (
          <motion.div
            key={i}
            className={`line ${l.kind}`}
            initial={{ opacity: 0, x: -6 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.2, ease: EASE }}
          >
            {l.text}
          </motion.div>
        ))}
        <div ref={endRef} />
      </div>
    </div>
  );
}
