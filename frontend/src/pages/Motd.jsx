import { useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";
import { api } from "../api/client.js";
import { riseItem } from "../components/motion.js";

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
      <div className="page-head">
        <div className="page-title">Template MOTD</div>
        <div className="page-sub">Éditez le message d'accueil. Les balises sont remplacées par les données réelles d'une VM.</div>
      </div>

      <div className="grid-2">
        <motion.div className="panel" variants={riseItem} initial="hidden" animate="show">
          <div className="panel-head"><h2>Éditeur</h2></div>
          <textarea style={{ minHeight: 300 }} value={template} onChange={(e) => setTemplate(e.target.value)} />
          <div style={{ marginTop: 16 }}>
            <div className="section-label">Balises disponibles — cliquez pour insérer</div>
            <div className="chips">
              {preview.tags.map((t) => <span key={t} className="chip" onClick={() => insertTag(t)}>{t}</span>)}
            </div>
          </div>
          {msg && <div className={`msg ${msg.ok ? "msg-ok" : "msg-err"}`}>{msg.text}</div>}
          <div className="btn-row"><button className="btn btn-primary" onClick={save}>Enregistrer le template</button></div>
        </motion.div>

        <motion.div className="panel" variants={riseItem} initial="hidden" animate="show">
          <div className="panel-head"><h2>Aperçu live {preview.vm_name ? <span className="badge badge-soft" style={{ marginLeft: 8 }}>{preview.vm_name}</span> : null}</h2></div>
          {preview.warning && <div className="msg msg-err">{preview.warning}</div>}
          <div className="terminal" style={{ height: 300 }}>
            <div className="line dim">{preview.rendered}</div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
