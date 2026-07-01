import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { api, openJobStream } from "../api/client.js";
import TypeSelector from "../components/TypeSelector.jsx";
import ProvisionConsole from "../components/ProvisionConsole.jsx";
import ConfirmDialog from "../components/ConfirmDialog.jsx";
import ProgressDialog from "../components/ProgressDialog.jsx";
import OsLogo from "../components/OsLogo.jsx";
import { relativeTime } from "../components/relativeTime.js";
import { IconSync, IconExternal, IconTrash, IconCheck, IconBolt } from "../components/icons.jsx";
import { stagger, riseItem, EASE } from "../components/motion.js";

export default function VMDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [vm, setVm] = useState(null);
  const [msg, setMsg] = useState(null);
  const [report, setReport] = useState(null);
  const [busy, setBusy] = useState(false);
  const [apt, setApt] = useState({ running: false, action: null, lines: [], progress: 0 });
  const [inspecting, setInspecting] = useState(false);
  const [confirmUpgrade, setConfirmUpgrade] = useState(false);
  const [deleteDialog, setDeleteDialog] = useState({
    open: false, phase: "confirm", progress: 0, message: "", success: false,
  });

  // Affiche d'abord les valeurs en cache, puis rafraîchit les infos système en SSH.
  useEffect(() => {
    let alive = true;
    api.getVm(id).then((v) => { if (alive) setVm(v); });
    setInspecting(true);
    api.inspectVm(id).then((v) => { if (alive) setVm(v); }).finally(() => { if (alive) setInspecting(false); });
    return () => { alive = false; };
  }, [id]);
  if (!vm) return <div className="empty">Chargement…</div>;

  async function refreshInfo() {
    setInspecting(true);
    try { setVm(await api.inspectVm(id)); } finally { setInspecting(false); }
  }

  function runApt(action) {
    if (apt.running) return;
    if (action === "upgrade") { setConfirmUpgrade(true); return; }
    startApt(action);
  }

  async function startApt(action) {
    setApt({ running: true, action, lines: [], progress: 0.05 });
    try {
      const { job_id } = await api.runApt(id, action);
      const es = openJobStream(job_id, (ev) => onApt(ev, es));
    } catch (e) {
      setApt((a) => ({ ...a, running: false, lines: [...a.lines, { text: `Erreur : ${e.message}`, kind: "err" }] }));
    }
  }

  function onApt(ev, stream) {
    setApt((a) => {
      const next = { ...a };
      if (ev.progress != null) next.progress = ev.progress;
      if (ev.type === "step") next.lines = [...a.lines, { text: `▸ ${ev.message}`, kind: "info" }];
      if (ev.type === "log") next.lines = [...a.lines, { text: ev.message, kind: "" }];
      if (ev.type === "result") {
        next.lines = [...a.lines, { text: ev.message, kind: ev.success ? "ok" : "err" }];
        next.running = false;
        stream.close();
        api.getVm(id).then(setVm);
      }
      return next;
    });
  }

  function set(key, val) { setVm((v) => ({ ...v, [key]: val })); }

  async function save() {
    setBusy(true); setMsg(null);
    try {
      await api.updateVm(id, {
        name: vm.name, vmid: Number(vm.vmid), static_ip: vm.static_ip, ports: vm.ports,
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

  function openDeleteDialog() {
    setDeleteDialog({ open: true, phase: "confirm", progress: 0, message: "", success: false });
  }

  async function confirmDelete() {
    setDeleteDialog((d) => ({ ...d, phase: "running", progress: 0.05, message: "Démarrage…" }));
    try {
      const { job_id } = await api.deleteVm(id);
      const es = openJobStream(job_id, (ev) => onDeleteEvent(ev, es));
    } catch (e) {
      setDeleteDialog((d) => ({ ...d, phase: "done", success: false, message: `Erreur : ${e.message}` }));
    }
  }

  function onDeleteEvent(ev, stream) {
    setDeleteDialog((d) => {
      const next = { ...d };
      if (ev.progress != null) next.progress = ev.progress;
      if (ev.type === "step" || ev.type === "log") next.message = ev.message;
      if (ev.type === "result") {
        next.phase = "done";
        next.success = ev.success;
        next.message = ev.message;
        stream.close();
      }
      return next;
    });
  }

  function closeDeleteDialog() {
    const wasSuccess = deleteDialog.success;
    setDeleteDialog({ open: false, phase: "confirm", progress: 0, message: "", success: false });
    if (wasSuccess) navigate("/");
  }

  return (
    <motion.div variants={stagger} initial="hidden" animate="show">
      <motion.div className="page-head" variants={riseItem}>
        <div className="page-title" style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <OsLogo osId={vm.os_id} size={26} /> {vm.name}
        </div>
        <div className="page-sub"><span className="mono">{vm.static_ip}</span> · {vm.provisioned ? "provisionnée" : "non provisionnée"}</div>
      </motion.div>

      <motion.div className="panel" variants={riseItem}>
        <div className="panel-head" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h2>Système</h2>
          <button className="btn btn-ghost btn-xs" onClick={refreshInfo} disabled={inspecting}>
            <IconSync /> {inspecting ? "Lecture…" : "Rafraîchir les infos"}
          </button>
        </div>
        <div className="sysgrid">
          <SysItem label="Système d'exploitation" value={
            <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
              <OsLogo osId={vm.os_id} size={16} /> {vm.os_name || "—"}
            </span>} />
          <SysItem label="Noyau" value={vm.kernel || "—"} mono />
          <SysItem label="Architecture" value={vm.arch || "—"} mono />
          <SysItem label="Interface réseau" value={vm.net_interface || "—"} mono />
          <SysItem label="IP actuelle" value={vm.current_ip || vm.static_ip} mono />
          <SysItem label="Mises à jour" value={
            vm.pending_updates > 0
              ? <span className="badge badge-xs badge-essentielle">{vm.pending_updates} disponible(s)</span>
              : <span className="badge badge-xs badge-ok">À jour</span>} />
        </div>
        <div className="btn-row" style={{ marginTop: 6 }}>
          {vm.pending_updates > 0 && (
            <button className="btn btn-primary" onClick={() => runApt("upgrade")} disabled={apt.running}>
              <IconBolt /> Mettre à jour ({vm.pending_updates})
            </button>
          )}
          <span className="stat-foot" style={{ alignSelf: "center" }}>
            {vm.sysinfo_at ? `Relevé ${relativeTime(vm.sysinfo_at)}` : "Jamais relevé"}
          </span>
        </div>
      </motion.div>

      <motion.div className="panel" variants={riseItem}>
        <div className="panel-head"><h2>Configuration</h2></div>
        <div className="grid-2">
          <div className="field"><label>Nom</label><input value={vm.name} onChange={(e) => set("name", e.target.value)} /></div>
          <div className="field"><label>VMID (conteneur LXC Proxmox)</label><input className="mono-input" type="number" value={vm.vmid} onChange={(e) => set("vmid", e.target.value)} /></div>
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
        <div className="panel-head"><h2>Maintenance système</h2></div>
        <p className="hint">Vérifie ou applique les mises à jour avec le gestionnaire de la machine (apt, dnf, pacman…) et suis la sortie en direct.</p>
        <div className="btn-row">
          <button className="btn btn-ghost" onClick={() => runApt("update")} disabled={apt.running}>
            <IconSync /> {apt.running && apt.action === "update" ? "Vérification…" : "Vérifier les mises à jour"}
          </button>
          <button className="btn btn-ghost" onClick={() => runApt("upgrade")} disabled={apt.running}>
            <IconBolt /> {apt.running && apt.action === "upgrade" ? "Mise à niveau…" : "Tout mettre à jour"}
          </button>
        </div>
        {(apt.running || apt.lines.length > 0) && (
          <motion.div style={{ marginTop: 16 }} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3, ease: EASE }}>
            <ProvisionConsole lines={apt.lines} progress={apt.progress} />
          </motion.div>
        )}
      </motion.div>

      <motion.div className="panel" variants={riseItem}>
        <div className="panel-head"><h2>Suppression</h2></div>
        <p className="hint">Désactive le streaming Netdata si la VM est joignable, puis la retire. Une VM éteinte n'est jamais supprimée automatiquement.</p>
        <button className="btn btn-danger" onClick={openDeleteDialog}><IconTrash /> Supprimer cette VM</button>
      </motion.div>

      <ConfirmDialog
        open={confirmUpgrade}
        title="Appliquer les mises à jour ?"
        message="Les paquets seront mis à niveau sur cette machine."
        confirmLabel="Mettre à jour"
        onConfirm={() => { setConfirmUpgrade(false); startApt("upgrade"); }}
        onCancel={() => setConfirmUpgrade(false)}
      />

      <ConfirmDialog
        open={deleteDialog.open && deleteDialog.phase === "confirm"}
        title="Supprimer cette VM ?"
        message={`« ${vm.name} » sera démantelée (Netdata, MOTD, retour DHCP) puis retirée définitivement. Cette action est irréversible.`}
        confirmLabel="Supprimer"
        danger
        onConfirm={confirmDelete}
        onCancel={() => setDeleteDialog((d) => ({ ...d, open: false }))}
      />

      <ProgressDialog
        open={deleteDialog.open && deleteDialog.phase !== "confirm"}
        title={`Suppression de « ${vm.name} »`}
        progress={deleteDialog.progress}
        message={deleteDialog.message}
        done={deleteDialog.phase === "done"}
        success={deleteDialog.success}
        onClose={closeDeleteDialog}
      />
    </motion.div>
  );
}

function SysItem({ label, value, mono = false }) {
  return (
    <div className="sysitem">
      <div className="sysitem-label">{label}</div>
      <div className={`sysitem-value ${mono ? "mono" : ""}`}>{value}</div>
    </div>
  );
}
