import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client.js";
import { TypeBadge, StatusBadge } from "../components/Badges.jsx";

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

  return (
    <div>
      <div className="page-title">Dashboard</div>
      <div className="page-sub">Vue d'ensemble du homelab</div>

      <div className="cards">
        <div className="card"><div className="num">{vms.length}</div><div className="label">VMs totales</div></div>
        <div className="card"><div className="num" style={{ color: "var(--online)" }}>{online}</div><div className="label">En ligne</div></div>
        <div className="card"><div className="num" style={{ color: "var(--text-dim)" }}>{vms.length - online}</div><div className="label">Hors ligne</div></div>
        <div className="card"><div className="num" style={{ color: "var(--essentielle)" }}>{pending}</div><div className="label">MAJ en attente</div></div>
      </div>

      <div className="panel">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h2>VMs enregistrées</h2>
          <button className="btn btn-ghost" onClick={() => load(true)} disabled={loading}>
            {loading ? "Ping en cours…" : "Rafraîchir les statuts"}
          </button>
        </div>
        {vms.length === 0 ? (
          <p className="muted">Aucune VM. Ajoutez-en une depuis « Ajouter une VM ».</p>
        ) : (
          <table>
            <thead>
              <tr><th>Nom</th><th>IP</th><th>Type</th><th>Statut</th><th>Dernière MAJ</th><th>Netdata</th></tr>
            </thead>
            <tbody>
              {vms.map((vm) => (
                <tr key={vm.id} onClick={() => navigate(`/vm/${vm.id}`)}>
                  <td>{vm.name}</td>
                  <td>{vm.static_ip}</td>
                  <td><TypeBadge type={vm.vm_type} /></td>
                  <td><StatusBadge online={vm.last_seen_online} /></td>
                  <td className="muted">{vm.last_update_applied || "—"}</td>
                  <td onClick={(e) => e.stopPropagation()}>
                    <a className="link-nd" href={`http://${vm.static_ip}:19999`} target="_blank" rel="noreferrer">Ouvrir →</a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
