import { useEffect, useState } from "react";
import { api } from "../api/client.js";

export default function Updates() {
  const [data, setData] = useState({ essentielles: [], standard: [] });
  useEffect(() => { api.getUpdates().then(setData); }, []);

  return (
    <div>
      <div className="page-title">Mises à jour</div>
      <div className="page-sub">Notifications pour les VMs Essentielles, historique pour les Standard.</div>

      <div className="panel">
        <h2 style={{ color: "var(--essentielle)" }}>Essentielles — MAJ en attente (action manuelle)</h2>
        {data.essentielles.length === 0 ? (
          <p className="muted">Aucune mise à jour en attente.</p>
        ) : (
          <table>
            <thead><tr><th>Nom</th><th>IP</th><th>MAJ disponibles</th><th>Dernier check</th></tr></thead>
            <tbody>
              {data.essentielles.map((v) => (
                <tr key={v.id}>
                  <td>{v.name}</td><td>{v.static_ip}</td>
                  <td style={{ color: "var(--essentielle)" }}>{v.pending} disponible(s)</td>
                  <td className="muted">{v.last_check || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="panel">
        <h2 style={{ color: "var(--standard)" }}>Standard — dernière MAJ automatique</h2>
        {data.standard.length === 0 ? (
          <p className="muted">Aucune VM Standard.</p>
        ) : (
          <table>
            <thead><tr><th>Nom</th><th>IP</th><th>Dernière MAJ appliquée</th></tr></thead>
            <tbody>
              {data.standard.map((v) => (
                <tr key={v.id}><td>{v.name}</td><td>{v.static_ip}</td><td className="muted">{v.last_update_applied || "Jamais"}</td></tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
