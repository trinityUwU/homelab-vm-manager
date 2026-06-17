import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { api, openJobStream } from "../api/client.js";
import TypeSelector from "../components/TypeSelector.jsx";
import ProvisionConsole from "../components/ProvisionConsole.jsx";
import { IconBolt, IconCheck } from "../components/icons.jsx";
import { riseItem, EASE } from "../components/motion.js";

const EMPTY = { name: "", dhcp_ip: "", static_ip: "", ports: "", vm_type: "standard", ssh_user: "", ssh_password: "" };

export default function AddVM() {
  const [form, setForm] = useState(EMPTY);
  const [sshOk, setSshOk] = useState(false);
  const [msg, setMsg] = useState(null);
  const [lines, setLines] = useState([]);
  const [progress, setProgress] = useState(0);
  const [provisioning, setProvisioning] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    api.getSettings().then((s) => setForm((f) => ({ ...f, ssh_user: s.ssh_user, ssh_password: s.ssh_password })));
  }, []);

  function set(key, val) {
    setForm((f) => ({ ...f, [key]: val }));
    setSshOk(false);
  }

  async function testSsh() {
    setMsg(null);
    const host = form.dhcp_ip || form.static_ip;
    try {
      const r = await api.testSsh({ host, ssh_user: form.ssh_user, ssh_password: form.ssh_password });
      setSshOk(r.ok);
      setMsg({ ok: r.ok, text: r.message });
    } catch (e) {
      setMsg({ ok: false, text: e.message });
    }
  }

  function addLine(text, kind = "") { setLines((ls) => [...ls, { text, kind }]); }

  async function provision() {
    setProvisioning(true);
    setLines([]);
    setProgress(0);
    try {
      const vm = await api.createVm(form);
      const { job_id } = await api.provision(vm.id);
      const es = openJobStream(job_id, (ev) => handleEvent(ev, es, vm.id));
    } catch (e) {
      addLine(`Erreur : ${e.message}`, "err");
      setProvisioning(false);
    }
  }

  function handleEvent(ev, stream, vmId) {
    if (ev.progress != null) setProgress(ev.progress);
    if (ev.type === "step") addLine(`▸ ${ev.message}`, "info");
    if (ev.type === "result") {
      addLine(ev.message, ev.success ? "ok" : "err");
      setProvisioning(false);
      stream.close();
      if (ev.success) setTimeout(() => navigate(`/vm/${vmId}`), 1600);
    }
  }

  const host = form.dhcp_ip || form.static_ip;
  const canTest = host && form.ssh_user && form.ssh_password;

  return (
    <div>
      <div className="page-head">
        <div className="page-title">Ajouter une VM</div>
        <div className="page-sub">Renseignez la VM, testez le SSH, puis lancez le provisioning automatique.</div>
      </div>

      <motion.div className="panel" variants={riseItem} initial="hidden" animate="show">
        <div className="grid-2">
          <div className="field"><label>Nom de la VM</label>
            <input value={form.name} onChange={(e) => set("name", e.target.value)} placeholder="ex : web-01" /></div>
          <div className="field"><label>Ports utilisés (optionnel — ex 22;80;5000)</label>
            <input className="mono-input" value={form.ports} onChange={(e) => set("ports", e.target.value)} placeholder="22;80;5000" /></div>
          <div className="field"><label>IP DHCP actuelle (vide si déjà en statique)</label>
            <input className="mono-input" value={form.dhcp_ip} onChange={(e) => set("dhcp_ip", e.target.value)} placeholder="192.168.1.50" /></div>
          <div className="field"><label>IP statique cible</label>
            <input className="mono-input" value={form.static_ip} onChange={(e) => set("static_ip", e.target.value)} placeholder="192.168.1.20" /></div>
          <div className="field"><label>Utilisateur SSH</label>
            <input className="mono-input" value={form.ssh_user} onChange={(e) => set("ssh_user", e.target.value)} /></div>
          <div className="field"><label>Mot de passe SSH</label>
            <input type="password" value={form.ssh_password} onChange={(e) => set("ssh_password", e.target.value)} /></div>
        </div>

        <div className="field" style={{ marginTop: 4 }}><label>Type de VM</label>
          <TypeSelector value={form.vm_type} onChange={(v) => set("vm_type", v)} /></div>

        {msg && (
          <motion.div className={`msg ${msg.ok ? "msg-ok" : "msg-err"}`} initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2, ease: EASE }}>
            {msg.text}
          </motion.div>
        )}

        <div className="btn-row">
          <button className="btn btn-ghost" onClick={testSsh} disabled={!canTest || provisioning}>
            {sshOk ? <IconCheck /> : null} Tester la connexion SSH
          </button>
          <button className="btn btn-primary" onClick={provision} disabled={!sshOk || !form.name || !form.static_ip || provisioning}>
            <IconBolt /> {provisioning ? "Provisioning…" : "Provisionner"}
          </button>
        </div>
      </motion.div>

      {(provisioning || lines.length > 0) && (
        <motion.div className="panel" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3, ease: EASE }}>
          <div className="panel-head"><h2>Provisioning en direct</h2></div>
          <ProvisionConsole lines={lines} progress={progress} />
        </motion.div>
      )}
    </div>
  );
}
