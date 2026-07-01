// Sélecteur du type de machine Proxmox — détermine où l'IP statique est posée
// (net0 côté hôte pour un LXC, /etc/network/interfaces côté invité pour QEMU).
import { motion } from "framer-motion";
import { EASE } from "./motion.js";

const OPTS = [
  { value: "lxc", name: "LXC", desc: "Conteneur Proxmox — IP statique posée côté hôte (net0)", color: "var(--standard)" },
  { value: "qemu", name: "QEMU", desc: "VM Debian pure — IP statique posée côté invité", color: "var(--essentielle)" },
  { value: "auto", name: "Auto", desc: "Détection au premier provisioning — VMID conseillé", color: "var(--text-muted)" },
];

export default function MachineTypeSelector({ value, onChange }) {
  return (
    <div className="type-toggle type-toggle-3">
      {OPTS.map((o) => (
        <motion.div
          key={o.value}
          className={`type-opt ${value === o.value ? "on-accent" : ""}`}
          style={{ "--opt-accent": o.color }}
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
