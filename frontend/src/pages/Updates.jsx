import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { api } from "../api/client.js";
import { stagger, riseItem } from "../components/motion.js";

export default function Updates() {
  const [data, setData] = useState({ essentielles: [], standard: [] });
  useEffect(() => { api.getUpdates().then(setData); }, []);

  return (
    <motion.div variants={stagger} initial="hidden" animate="show">
      <motion.div className="page-head" variants={riseItem}>
        <div className="page-title">Mises à jour</div>
        <div className="page-sub">Notifications pour les Essentielles, historique pour les Standard.</div>
      </motion.div>

      <motion.div className="panel" variants={riseItem}>
        <div className="panel-head"><h2 style={{ color: "var(--essentielle)" }}>Essentielles — action manuelle requise</h2></div>
        {data.essentielles.length === 0 ? (
          <div className="empty">Aucune mise à jour en attente.</div>
        ) : (
          <table className="tbl">
            <thead><tr><th>Nom</th><th>IP</th><th>MAJ disponibles</th><th>Dernier check</th></tr></thead>
            <tbody>
              {data.essentielles.map((v) => (
                <tr key={v.id} style={{ cursor: "default" }}>
                  <td>{v.name}</td><td className="mono">{v.static_ip}</td>
                  <td style={{ color: "var(--essentielle)", fontWeight: 540 }}>{v.pending} disponible(s)</td>
                  <td className="muted">{v.last_check || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </motion.div>

      <motion.div className="panel" variants={riseItem}>
        <div className="panel-head"><h2 style={{ color: "var(--standard)" }}>Standard — dernière MAJ automatique</h2></div>
        {data.standard.length === 0 ? (
          <div className="empty">Aucune VM Standard.</div>
        ) : (
          <table className="tbl">
            <thead><tr><th>Nom</th><th>IP</th><th>Dernière MAJ appliquée</th></tr></thead>
            <tbody>
              {data.standard.map((v) => (
                <tr key={v.id} style={{ cursor: "default" }}><td>{v.name}</td><td className="mono">{v.static_ip}</td><td className="muted">{v.last_update_applied || "Jamais"}</td></tr>
              ))}
            </tbody>
          </table>
        )}
      </motion.div>
    </motion.div>
  );
}
