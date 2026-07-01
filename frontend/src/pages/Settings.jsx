import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { api } from "../api/client.js";
import { stagger, riseItem } from "../components/motion.js";

export default function Settings() {
  const [s, setS] = useState(null);
  const [msg, setMsg] = useState(null);

  useEffect(() => { api.getSettings().then(setS); }, []);
  if (!s) return <div className="empty">Chargement…</div>;

  function set(key, val) { setS((cur) => ({ ...cur, [key]: val })); }

  async function save() {
    setMsg(null);
    try {
      await api.saveSettings(s);
      window.dispatchEvent(new CustomEvent("settings-updated", { detail: s }));
      setMsg({ ok: true, text: "Paramètres enregistrés" });
    } catch (e) { setMsg({ ok: false, text: e.message }); }
    setTimeout(() => setMsg(null), 2500);
  }

  return (
    <motion.div variants={stagger} initial="hidden" animate="show">
      <motion.div className="page-head" variants={riseItem}>
        <div className="page-title">Paramètres globaux</div>
        <div className="page-sub">SSH par défaut, Netdata, texte fixe du MOTD. La planification est dans « Mises à jour ».</div>
      </motion.div>

      <motion.div className="panel" variants={riseItem}>
        <div className="panel-head"><h2>SSH par défaut</h2></div>
        <p className="hint">Pré-remplit le formulaire d'ajout — vos VMs partagent souvent le même template Proxmox.</p>
        <div className="grid-2">
          <div className="field"><label>Utilisateur SSH</label><input className="mono-input" value={s.ssh_user} onChange={(e) => set("ssh_user", e.target.value)} /></div>
          <div className="field"><label>Mot de passe SSH</label><input type="password" value={s.ssh_password} onChange={(e) => set("ssh_password", e.target.value)} /></div>
        </div>
      </motion.div>

      <motion.div className="panel" variants={riseItem}>
        <div className="panel-head"><h2>Hôte Proxmox</h2></div>
        <p className="hint">Requis pour les LXC : seul l'hôte peut poser une IP statique persistante sur un conteneur (net0 via <code>pct set</code>), pas l'intérieur de l'invité.</p>
        <div className="grid-2">
          <div className="field"><label>Hôte / IP</label><input className="mono-input" value={s.proxmox_host} onChange={(e) => set("proxmox_host", e.target.value)} placeholder="192.168.1.10" /></div>
          <div className="field"><label>Utilisateur SSH</label><input className="mono-input" value={s.proxmox_ssh_user} onChange={(e) => set("proxmox_ssh_user", e.target.value)} /></div>
          <div className="field"><label>Mot de passe SSH</label><input type="password" value={s.proxmox_ssh_password} onChange={(e) => set("proxmox_ssh_password", e.target.value)} /></div>
        </div>
      </motion.div>

      <motion.div className="panel" variants={riseItem}>
        <div className="panel-head"><h2>Netdata central</h2></div>
        <div className="grid-2">
          <div className="field"><label>URL du parent</label><input className="mono-input" value={s.netdata_parent_url} onChange={(e) => set("netdata_parent_url", e.target.value)} /></div>
          <div className="field"><label>Clé API de streaming (uuidgen sur le parent)</label><input className="mono-input" value={s.netdata_api_key} onChange={(e) => set("netdata_api_key", e.target.value)} placeholder="uuid…" /></div>
        </div>
      </motion.div>

      <motion.div className="panel" variants={riseItem}>
        <div className="panel-head"><h2>MOTD — texte fixe</h2></div>
        <div className="grid-2">
          <div className="field"><label>Nom du lab — {"{{LAB_NAME}}"}</label><input value={s.lab_name} onChange={(e) => set("lab_name", e.target.value)} /></div>
          <div className="field"><label>Ligne personnalisée — {"{{LAB_LINE}}"}</label><input value={s.lab_line} onChange={(e) => set("lab_line", e.target.value)} /></div>
        </div>
      </motion.div>

      <motion.div className="panel" variants={riseItem}>
        <div className="panel-head"><h2>Notifications</h2></div>
        <p className="hint">Affiche une notification en bas à droite quand une machine est mise à jour ou resynchronisée.</p>
        <label className="switch field" style={{ margin: 0 }}>
          <input type="checkbox" checked={s.notifications_enabled !== false} onChange={(e) => set("notifications_enabled", e.target.checked)} />
          <span>Activer les notifications temps réel</span>
        </label>
      </motion.div>

      {msg && <div className={`msg ${msg.ok ? "msg-ok" : "msg-err"}`}>{msg.text}</div>}
      <button className="btn btn-primary" onClick={save}>Enregistrer tous les paramètres</button>
    </motion.div>
  );
}
