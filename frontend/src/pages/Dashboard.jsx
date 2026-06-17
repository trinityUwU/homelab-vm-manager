import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { api } from "../api/client.js";
import { TypeBadge, StatusBadge } from "../components/Badges.jsx";
import AnimatedNumber from "../components/AnimatedNumber.jsx";
import { IconRefresh, IconExternal, IconServer } from "../components/icons.jsx";
import { stagger, riseItem } from "../components/motion.js";

const TILES = [
  { key: "total", label: "VMs totales", glow: "rgba(74,158,255,0.18)", color: "var(--text-primary)" },
  { key: "online", label: "En ligne", glow: "rgba(0,216,138,0.20)", color: "var(--online)" },
  { key: "offline", label: "Hors ligne", glow: "rgba(255,255,255,0.05)", color: "var(--text-muted)" },
  { key: "pending", label: "MAJ en attente", glow: "rgba(240,160,48,0.18)", color: "var(--essentielle)" },
];

export default function Dashboard() {
  const [vms, setVms] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  async function load(refresh) {
    setLoading(true);
    const data = refresh ? await api.refreshVms() : await api.listVms();
    setVms(data);
    setLoading(false);
  }
  useEffect(() => { load(false); }, []);

  const online = vms.filter((v) => v.last_seen_online).length;
  const pending = vms.reduce((n, v) => n + (v.pending_updates || 0), 0);
  const counts = { total: vms.length, online, offline: vms.length - online, pending };

  return (
    <div>
      <div className="page-head">
        <div className="page-title">Dashboard</div>
        <div className="page-sub">Vue d'ensemble du homelab</div>
      </div>

      <motion.div className="bento" variants={stagger} initial="hidden" animate="show">
        {TILES.map((t) => (
          <motion.div key={t.key} className="tile tile--glow" variants={riseItem} style={{ "--glow": t.glow }}>
            <div className="stat-label">{t.label}</div>
            <div className="stat-num" style={{ color: t.color }}><AnimatedNumber value={counts[t.key]} /></div>
            <div className="stat-foot">{t.key === "total" ? "enregistrées" : t.key === "pending" ? "paquets" : "machines"}</div>
          </motion.div>
        ))}
      </motion.div>

      <motion.div className="panel" variants={riseItem} initial="hidden" animate="show">
        <div className="panel-head">
          <h2>VMs enregistrées</h2>
          <button className="btn btn-ghost" onClick={() => load(true)} disabled={loading}>
            <IconRefresh /> {loading ? "Ping en cours…" : "Rafraîchir"}
          </button>
        </div>

        {vms.length === 0 ? (
          <div className="empty">Aucune VM enregistrée. Ajoutez-en une depuis « Ajouter une VM ».</div>
        ) : (
          <table className="tbl">
            <thead>
              <tr><th>Nom</th><th>IP statique</th><th>Type</th><th>Statut</th><th>Dernière MAJ</th><th>Netdata</th></tr>
            </thead>
            <motion.tbody variants={stagger} initial="hidden" animate="show">
              {vms.map((vm) => (
                <motion.tr key={vm.id} variants={riseItem} onClick={() => navigate(`/vm/${vm.id}`)}>
                  <td style={{ display: "flex", alignItems: "center", gap: 9 }}><IconServer width={15} height={15} style={{ opacity: 0.5 }} /> {vm.name}</td>
                  <td className="mono">{vm.static_ip}</td>
                  <td><TypeBadge type={vm.vm_type} /></td>
                  <td><StatusBadge online={vm.last_seen_online} /></td>
                  <td className="muted">{vm.last_update_applied || "—"}</td>
                  <td onClick={(e) => e.stopPropagation()}>
                    <a className="link-ext" href={`http://${vm.static_ip}:19999`} target="_blank" rel="noreferrer">Ouvrir <IconExternal width={13} height={13} /></a>
                  </td>
                </motion.tr>
              ))}
            </motion.tbody>
          </table>
        )}
      </motion.div>
    </div>
  );
}
