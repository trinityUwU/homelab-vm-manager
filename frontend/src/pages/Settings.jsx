import { useEffect, useState } from "react";
import { api } from "../api/client.js";

export default function Settings() {
  const [s, setS] = useState(null);
  const [msg, setMsg] = useState(null);

  useEffect(() => { api.getSettings().then(setS); }, []);
  if (!s) return <div className="muted">Chargement…</div>;

  function set(key, val) { setS((cur) => ({ ...cur, [key]: val })); }

  async function save() {
    setMsg(null);
    try {
      await api.saveSettings(s);
      setMsg({ ok: true, text: "Paramètres enregistrés" });
    } catch (e) { setMsg({ ok: false, text: e.message }); }
    setTimeout(() => setMsg(null), 2500);
  }

  return (
    <div>
      <div className="page-title">Paramètres globaux</div>
      <div className="page-sub">Identifiants SSH par défaut, Netdata, vérification quotidienne, texte du MOTD.</div>

      <div className="panel">
        <h2>SSH par défaut (pré-remplit le formulaire d'ajout)</h2>
        <div className="grid-2">
          <div className="field"><label>Utilisateur SSH</label><input value={s.ssh_user} onChange={(e) => set("ssh_user", e.target.value)} /></div>
          <div className="field"><label>Mot de passe SSH</label><input type="password" value={s.ssh_password} onChange={(e) => set("ssh_password", e.target.value)} /></div>
        </div>
      </div>

      <div className="panel">
        <h2>Netdata central</h2>
        <div className="grid-2">
          <div className="field"><label>URL du parent</label><input value={s.netdata_parent_url} onChange={(e) => set("netdata_parent_url", e.target.value)} /></div>
          <div className="field"><label>Clé API de streaming (générée sur le parent via uuidgen)</label><input value={s.netdata_api_key} onChange={(e) => set("netdata_api_key", e.target.value)} placeholder="uuid…" /></div>
        </div>
      </div>

      <div className="panel">
        <h2>Vérification quotidienne</h2>
        <div className="field" style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <input type="checkbox" style={{ width: "auto" }} checked={s.daily_check_enabled} onChange={(e) => set("daily_check_enabled", e.target.checked)} />
          <span>Activer le check automatique quotidien</span>
        </div>
        <div className="grid-2">
          <div className="field"><label>Heure</label><input type="number" min="0" max="23" value={s.daily_check_hour} onChange={(e) => set("daily_check_hour", Number(e.target.value))} /></div>
          <div className="field"><label>Minute</label><input type="number" min="0" max="59" value={s.daily_check_minute} onChange={(e) => set("daily_check_minute", Number(e.target.value))} /></div>
        </div>
      </div>

      <div className="panel">
        <h2>MOTD — texte fixe</h2>
        <div className="grid-2">
          <div className="field"><label>Nom du lab ({"{{LAB_NAME}}"})</label><input value={s.lab_name} onChange={(e) => set("lab_name", e.target.value)} /></div>
          <div className="field"><label>Ligne personnalisée ({"{{LAB_LINE}}"})</label><input value={s.lab_line} onChange={(e) => set("lab_line", e.target.value)} /></div>
        </div>
      </div>

      {msg && <div className={`msg ${msg.ok ? "msg-ok" : "msg-err"}`}>{msg.text}</div>}
      <button className="btn" onClick={save}>Enregistrer tous les paramètres</button>
    </div>
  );
}
