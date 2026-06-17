import { useEffect, useState, useCallback } from "react";
import { api } from "../api/client.js";

export default function Motd() {
  const [template, setTemplate] = useState("");
  const [preview, setPreview] = useState({ rendered: "", tags: [] });
  const [msg, setMsg] = useState(null);

  useEffect(() => { api.getMotd().then((d) => setTemplate(d.template)); }, []);

  const refresh = useCallback(async (tpl) => {
    try { setPreview(await api.previewMotd(tpl)); } catch { /* ignore */ }
  }, []);

  useEffect(() => {
    const t = setTimeout(() => refresh(template), 250);
    return () => clearTimeout(t);
  }, [template, refresh]);

  async function save() {
    await api.saveMotd(template);
    setMsg({ ok: true, text: "Template MOTD enregistré" });
    setTimeout(() => setMsg(null), 2000);
  }

  function insertTag(tag) { setTemplate((t) => t + tag); }

  return (
    <div>
      <div className="page-title">Template MOTD</div>
      <div className="page-sub">Éditez le message d'accueil. Les balises sont remplacées par les données réelles d'une VM.</div>

      <div className="grid-2">
        <div className="panel">
          <h2>Éditeur</h2>
          <textarea style={{ minHeight: 280 }} value={template} onChange={(e) => setTemplate(e.target.value)} />
          <div style={{ marginTop: 14 }}>
            <label>Balises disponibles (cliquez pour insérer)</label>
            {preview.tags.map((t) => <span key={t} className="tag-chip" onClick={() => insertTag(t)}>{t}</span>)}
          </div>
          {msg && <div className={`msg ${msg.ok ? "msg-ok" : "msg-err"}`}>{msg.text}</div>}
          <div className="btn-row"><button className="btn" onClick={save}>Enregistrer le template</button></div>
        </div>

        <div className="panel">
          <h2>Aperçu en direct {preview.vm_name ? `(${preview.vm_name})` : ""}</h2>
          {preview.warning && <div className="msg msg-err">{preview.warning}</div>}
          <div className="terminal" style={{ height: 280 }}>
            <div className="line">{preview.rendered}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
