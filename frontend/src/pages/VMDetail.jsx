import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { api } from "../api/client.js";
import TypeSelector from "../components/TypeSelector.jsx";
import { IconSync, IconExternal, IconTrash, IconCheck } from "../components/icons.jsx";
import { stagger, riseItem, EASE } from "../components/motion.js";

export default function VMDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [vm, setVm] = useState(null);
  const [msg, setMsg] = useState(null);
  const [report, setReport] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => { api.getVm(id).then(setVm); }, [id]);
  if (!vm) return <div className="empty">Chargement…</div>;

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
    try { setReport(await api.syncVm(id)); }
    catch (e) { setMsg({ ok: false, text: e.message }); }
    setBusy(false);
  }

  async function remove() {
    if (!confirm(`Supprimer « ${vm.name} » ? Cette action est définitive.`)) return;
    const r = await api.deleteVm(id);
    alert(r.message);
    navigate("/");
  }

  return (
    <motion.div variants={stagger} initial="hidden" animate="show">
      <motion.div className="page-head" variants={riseItem}>
        <div className="page-title">{vm.name}</div>
        <div className="page-sub"><span className="mono">{vm.static_ip}</span> · {vm.provisioned ? "provisionnée" : "non provisionnée"}</div>
      </motion.div>

      <motion.div className="panel" variants={riseItem}>
        <div className="panel-head"><h2>Configuration</h2></div>
        <div className="grid-2">
          <div className="field"><label>Nom</label><input value={vm.name} onChange={(e) => set("name", e.target.value)} /></div>
          <div className="field"><label>IP statique</label><input className="mono-input" value={vm.static_ip} onChange={(e) => set("static_ip", e.target.value)} /></div>
          <div className="field"><label>Ports</label><input className="mono-input" value={vm.ports} onChange={(e) => set("ports", e.target.value)} /></div>
          <div className="field"><label>Utilisateur SSH</label><input className="mono-input" value={vm.ssh_user} onChange={(e) => set("ssh_user", e.target.value)} /></div>
          <div className="field"><label>Mot de passe SSH</label><input type="password" value={vm.ssh_password} onChange={(e) => set("ssh_password", e.target.value)} /></div>
        </div>
        <div className="field"><label>Type</label><TypeSelector value={vm.vm_type} onChange={(v) => set("vm_type", v)} /></div>
        {msg && <div className={`msg ${msg.ok ? "msg-ok" : "msg-err"}`}>{msg.text}</div>}
        <div className="btn-row">
          <button className="btn btn-primary" onClick={save} disabled={busy}>Enregistrer</button>
          <a className="btn btn-ghost" href={`http://${vm.static_ip}:19999`} target="_blank" rel="noreferrer"><IconExternal /> Dashboard Netdata</a>
        </div>
      </motion.div>

      <motion.div className="panel" variants={riseItem}>
        <div className="panel-head"><h2>Vérifier &amp; Synchroniser</h2></div>
        <p className="hint">Connexion SSH, contrôle IP / MOTD / Netdata. Ne corrige que ce qui s'écarte du template — idempotent.</p>
        <button className="btn btn-ghost" onClick={sync} disabled={busy}><IconSync /> {busy ? "Vérification…" : "Lancer la vérification"}</button>

        {report && !report.ok && <div className="msg msg-err">{report.error}</div>}
        {report && report.ok && (
          <motion.div style={{ marginTop: 16 }} variants={stagger} initial="hidden" animate="show">
            {report.items.map((it, i) => (
              <motion.div className="report-line" key={i} variants={riseItem}>
                <span className={`report-tag ${it.status === "ok" ? "ok" : "fix"}`}>
                  {it.status === "ok" ? <><IconCheck width={14} height={14} /> OK</> : "Corrigé"}
                </span>
                <strong style={{ minWidth: 96 }}>{it.point}</strong>
                <span className="muted">{it.detail}</span>
              </motion.div>
            ))}
          </motion.div>
        )}
      </motion.div>

      <motion.div className="panel" variants={riseItem}>
        <div className="panel-head"><h2>Suppression</h2></div>
        <p className="hint">Désactive le streaming Netdata si la VM est joignable, puis la retire. Une VM éteinte n'est jamais supprimée automatiquement.</p>
        <button className="btn btn-danger" onClick={remove}><IconTrash /> Supprimer cette VM</button>
      </motion.div>
    </motion.div>
  );
}
