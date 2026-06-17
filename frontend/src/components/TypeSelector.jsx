// Sélecteur de type de VM, bleu (Standard) ou orange (Essentielle) sans ambiguïté.
import { motion } from "framer-motion";
import { EASE } from "./motion.js";

const OPTS = [
  { value: "standard", name: "Standard", desc: "Mises à jour appliquées automatiquement", color: "var(--standard)" },
  { value: "essentielle", name: "Essentielle", desc: "MAJ vérifiées mais jamais appliquées seules", color: "var(--essentielle)" },
];

export default function TypeSelector({ value, onChange }) {
  return (
    <div className="type-toggle">
      {OPTS.map((o) => (
        <motion.div
          key={o.value}
          className={`type-opt ${value === o.value ? `on-${o.value}` : ""}`}
          onClick={() => onChange(o.value)}
          whileHover={{ y: -2 }}
          transition={{ duration: 0.16, ease: EASE }}
        >
          <div className="t-name"><span className="t-chip" style={{ background: o.color }} /> {o.name}</div>
          <div className="t-desc">{o.desc}</div>
        </motion.div>
      ))}
    </div>
  );
}
