import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, openJobSocket } from "../api/client.js";
import TypeSelector from "../components/TypeSelector.jsx";
import ProvisionConsole from "../components/ProvisionConsole.jsx";

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
    // Pré-remplit user/mot de passe SSH depuis les paramètres globaux.
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

  function addLine(text, kind = "") {
    setLines((ls) => [...ls, { text, kind }]);
  }

  async function provision() {
    setProvisioning(true);
    setLines([]);
    setProgress(0);
    try {
      const vm = await api.createVm(form);
      const { job_id } = await api.provision(vm.id);
      const ws = openJobSocket(job_id, (ev) => handleEvent(ev, ws, vm.id));
    } catch (e) {
      addLine(`Erreur : ${e.message}`, "err");
      setProvisioning(false);
    }
  }

  function handleEvent(ev, ws, vmId) {
    if (ev.progress != null) setProgress(ev.progress);
    if (ev.type === "step") addLine(`▸ ${ev.message}`, "info");
    if (ev.type === "result") {
      addLine(ev.message, ev.success ? "ok" : "err");
      setProvisioning(false);
      ws.close();
      if (ev.success) setTimeout(() => navigate(`/vm/${vmId}`), 1500);
    }
  }

  const host = form.dhcp_ip || form.static_ip;
  const canTest = host && form.ssh_user && form.ssh_password;

  return (
    <div>
      <div className="page-title">Ajouter une VM</div>
      <div className="page-sub">Renseignez la VM, testez le SSH, puis provisionnez automatiquement.</div>

      <div className="panel">
        <div className="grid-2">
          <div className="field"><label>Nom de la VM</label>
            <input value={form.name} onChange={(e) => set("name", e.target.value)} placeholder="ex : web-01" /></div>
          <div className="field"><label>Ports utilisés (optionnel, ex 22;80;5000)</label>
            <input value={form.ports} onChange={(e) => set("ports", e.target.value)} placeholder="22;80;5000" /></div>
          <div className="field"><label>IP DHCP actuelle (vide si déjà en statique)</label>
            <input value={form.dhcp_ip} onChange={(e) => set("dhcp_ip", e.target.value)} placeholder="192.168.1.50" /></div>
          <div className="field"><label>IP statique cible</label>
            <input value={form.static_ip} onChange={(e) => set("static_ip", e.target.value)} placeholder="192.168.1.20" /></div>
          <div className="field"><label>Utilisateur SSH</label>
            <input value={form.ssh_user} onChange={(e) => set("ssh_user", e.target.value)} /></div>
          <div className="field"><label>Mot de passe SSH</label>
            <input type="password" value={form.ssh_password} onChange={(e) => set("ssh_password", e.target.value)} /></div>
        </div>

        <div className="field"><label>Type de VM</label>
          <TypeSelector value={form.vm_type} onChange={(v) => set("vm_type", v)} /></div>

        {msg && <div className={`msg ${msg.ok ? "msg-ok" : "msg-err"}`}>{msg.text}</div>}

        <div className="btn-row">
          <button className="btn btn-ghost" onClick={testSsh} disabled={!canTest || provisioning}>
            Tester la connexion SSH
          </button>
          <button className="btn" onClick={provision} disabled={!sshOk || !form.name || !form.static_ip || provisioning}>
            {provisioning ? "Provisioning en cours…" : "Provisionner"}
          </button>
        </div>
      </div>

      {(provisioning || lines.length > 0) && (
        <div className="panel">
          <h2>Provisioning</h2>
          <ProvisionConsole lines={lines} progress={progress} />
        </div>
      )}
    </div>
  );
}
