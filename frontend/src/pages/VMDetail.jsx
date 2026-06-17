import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../api/client.js";
import TypeSelector from "../components/TypeSelector.jsx";

export default function VMDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [vm, setVm] = useState(null);
  const [msg, setMsg] = useState(null);
  const [report, setReport] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => { api.getVm(id).then(setVm); }, [id]);
  if (!vm) return <div className="muted">Chargement…</div>;

  function set(key, val) { setVm((v) => ({ ...v, [key]: val })); }

  async function save() {
    setBusy(true); setMsg(null);
    try {
      await api.updateVm(id, {
        name: vm.name, static_ip: vm.static_ip, ports: vm.ports,
        vm_type: vm.vm_type, ssh_user: vm.ssh_user, ssh_password: vm.ssh_password,
      });
      setMsg({ ok: true, text: "Modifications enregistrées" });
    } catch (e) { setMsg({ ok: false, text: e.message }); }
    setBusy(false);
  }

  async function sync() {
    setBusy(true); setReport(null); setMsg(null);
    try {
      const r = await api.syncVm(id);
      setReport(r);
    } catch (e) { setMsg({ ok: false, text: e.message }); }
    setBusy(false);
  }

  async function remove() {
    if (!confirm(`Supprimer « ${vm.name} » ? Cette action est définitive.`)) return;
    const r = await api.deleteVm(id);
    alert(r.message);
    navigate("/");
  }

  return (
    <div>
      <div className="page-title">{vm.name}</div>
      <div className="page-sub">{vm.static_ip} · {vm.provisioned ? "provisionnée" : "non provisionnée"}</div>

      <div className="panel">
        <h2>Modifier</h2>
        <div className="grid-2">
          <div className="field"><label>Nom</label><input value={vm.name} onChange={(e) => set("name", e.target.value)} /></div>
          <div className="field"><label>IP statique</label><input value={vm.static_ip} onChange={(e) => set("static_ip", e.target.value)} /></div>
          <div className="field"><label>Ports</label><input value={vm.ports} onChange={(e) => set("ports", e.target.value)} /></div>
          <div className="field"><label>Utilisateur SSH</label><input value={vm.ssh_user} onChange={(e) => set("ssh_user", e.target.value)} /></div>
          <div className="field"><label>Mot de passe SSH</label><input type="password" value={vm.ssh_password} onChange={(e) => set("ssh_password", e.target.value)} /></div>
        </div>
        <div className="field"><label>Type</label><TypeSelector value={vm.vm_type} onChange={(v) => set("vm_type", v)} /></div>
        {msg && <div className={`msg ${msg.ok ? "msg-ok" : "msg-err"}`}>{msg.text}</div>}
        <div className="btn-row">
          <button className="btn" onClick={save} disabled={busy}>Enregistrer</button>
          <a className="btn btn-ghost" href={`http://${vm.static_ip}:19999`} target="_blank" rel="noreferrer">Dashboard Netdata →</a>
        </div>
      </div>

      <div className="panel">
        <h2>Vérifier & Synchroniser</h2>
        <p className="muted">Connexion SSH, vérifie IP / MOTD / Netdata. Ne touche qu'à ce qui est incorrect.</p>
        <button className="btn btn-ghost" onClick={sync} disabled={busy} style={{ marginTop: 12 }}>
          {busy ? "Vérification…" : "Lancer la vérification"}
        </button>
        {report && !report.ok && <div className="msg msg-err">{report.error}</div>}
        {report && report.ok && (
          <div style={{ marginTop: 16 }}>
            {report.items.map((it, i) => (
              <div className="report-line" key={i}>
                <span style={{ color: it.status === "ok" ? "var(--online)" : "var(--essentielle)", minWidth: 80 }}>
                  {it.status === "ok" ? "OK" : "Corrigé"}
                </span>
                <strong style={{ minWidth: 110 }}>{it.point}</strong>
                <span className="muted">{it.detail}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="panel">
        <h2>Suppression</h2>
        <p className="muted">Désactive le streaming Netdata si la VM est joignable, puis retire la VM. Une VM éteinte n'est jamais supprimée automatiquement.</p>
        <button className="btn btn-danger" onClick={remove} style={{ marginTop: 12 }}>Supprimer cette VM</button>
      </div>
    </div>
  );
}
