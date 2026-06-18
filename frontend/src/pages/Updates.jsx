import { useEffect, useState, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import { api } from "../api/client.js";
import { useLive } from "../components/live/LiveContext.jsx";
import { stagger, riseItem } from "../components/motion.js";
import { KindBadge, ModeBadge, ReasonBadge, StatusBadge } from "../components/HistoryBadges.jsx";

export default function Updates() {
  const [searchParams] = useSearchParams();
  const { version } = useLive();
  const [overview, setOverview] = useState({ essentielles: [], machines: [] });
  const [settings, setSettings] = useState(null);
  const [history, setHistory] = useState([]);
  const [filter, setFilter] = useState({ vmId: searchParams.get("vm") || "", kind: "" });

  const loadOverview = useCallback(() => api.getUpdates().then(setOverview), []);
  const loadHistory = useCallback(
    () => api.getHistory({ vmId: filter.vmId, kind: filter.kind }).then(setHistory),
    [filter.vmId, filter.kind],
  );

  // Toast cliqué « Mises à jour » → filtre automatiquement sur la machine ciblée.
  useEffect(() => { setFilter((f) => ({ ...f, vmId: searchParams.get("vm") || "" })); }, [searchParams]);
  useEffect(() => { api.getSettings().then(setSettings); }, []);
  // Rafraîchissement temps réel : `version` est bumpé à chaque événement reçu.
  useEffect(() => { loadOverview(); }, [loadOverview, version]);
  useEffect(() => { loadHistory(); }, [loadHistory, version]);

  return (
    <motion.div variants={stagger} initial="hidden" animate="show">
      <motion.div className="page-head" variants={riseItem}>
        <div className="page-title">Mises à jour</div>
        <div className="page-sub">Planification, machines surveillées et historique des scans &amp; resynchronisations.</div>
      </motion.div>

      {settings && <Planning settings={settings} onSettings={setSettings} onRan={() => setTimeout(() => { loadOverview(); loadHistory(); }, 1500)} />}
      <Machines machines={overview.machines} onToggle={loadOverview} />
      <Essentielles list={overview.essentielles} />
      <History rows={history} machines={overview.machines} filter={filter} setFilter={setFilter} />
    </motion.div>
  );
}

function Planning({ settings, onSettings, onRan }) {
  const [saving, setSaving] = useState(false);
  const [running, setRunning] = useState(false);
  const set = (k, v) => onSettings((s) => ({ ...s, [k]: v }));

  async function save() {
    setSaving(true);
    const keys = ["daily_check_enabled", "daily_check_hour", "daily_check_minute", "auto_resync_on_config_change"];
    await api.saveSettings(Object.fromEntries(keys.map((k) => [k, settings[k]])));
    setSaving(false);
  }
  async function runNow() {
    setRunning(true);
    await api.runScanNow();
    onRan();
    setTimeout(() => setRunning(false), 1500);
  }

  return (
    <motion.div className="panel" variants={riseItem}>
      <div className="panel-head"><h2>Planification</h2></div>
      <label className="switch field" style={{ marginBottom: 16 }}>
        <input type="checkbox" checked={settings.daily_check_enabled} onChange={(e) => set("daily_check_enabled", e.target.checked)} />
        <span>Vérifier automatiquement chaque jour</span>
      </label>
      <div className="grid-2">
        <div className="field"><label>Heure de vérification</label><input type="number" min="0" max="23" value={settings.daily_check_hour} onChange={(e) => set("daily_check_hour", Number(e.target.value))} /></div>
        <div className="field"><label>Minute</label><input type="number" min="0" max="59" value={settings.daily_check_minute} onChange={(e) => set("daily_check_minute", Number(e.target.value))} /></div>
      </div>
      <label className="switch field" style={{ marginTop: 6 }}>
        <input type="checkbox" checked={settings.auto_resync_on_config_change} onChange={(e) => set("auto_resync_on_config_change", e.target.checked)} />
        <span>Resynchroniser automatiquement les VMs quand une config (MOTD, lab) change</span>
      </label>
      <div className="btn-row" style={{ marginTop: 16, display: "flex", gap: 10 }}>
        <button className="btn btn-primary" onClick={save} disabled={saving}>{saving ? "Enregistrement…" : "Enregistrer la planification"}</button>
        <button className="btn btn-ghost" onClick={runNow} disabled={running}>{running ? "Scan lancé…" : "Lancer un scan maintenant"}</button>
      </div>
    </motion.div>
  );
}

function Machines({ machines, onToggle }) {
  async function toggle(vm) {
    await api.updateVm(vm.id, { scan_excluded: !vm.scan_excluded });
    onToggle();
  }
  return (
    <motion.div className="panel" variants={riseItem}>
      <div className="panel-head"><h2>Machines surveillées</h2></div>
      <p className="hint">Décochez une machine pour l'exclure du scan automatique et des resynchronisations de config.</p>
      {machines.length === 0 ? <div className="empty">Aucune VM enregistrée.</div> : (
        <table className="tbl">
          <thead><tr><th>Machine</th><th>IP</th><th>Type</th><th>Dernier scan</th><th>Surveillée</th></tr></thead>
          <tbody>
            {machines.map((m) => (
              <tr key={m.id} style={{ cursor: "default" }}>
                <td>{m.name}</td>
                <td className="mono">{m.static_ip}</td>
                <td><span className={`badge badge-xs ${m.vm_type === "essentielle" ? "badge-essentielle" : "badge-standard"}`}>{m.vm_type === "essentielle" ? "Notifié" : "MAJ auto"}</span></td>
                <td className="muted">{m.last_check || "—"}</td>
                <td>
                  <label className="switch" style={{ margin: 0 }}>
                    <input type="checkbox" checked={!m.scan_excluded} onChange={() => toggle(m)} />
                    <span className="muted">{m.scan_excluded ? "Exclue" : "Incluse"}</span>
                  </label>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </motion.div>
  );
}

function Essentielles({ list }) {
  if (list.length === 0) return null;
  return (
    <motion.div className="panel" variants={riseItem}>
      <div className="panel-head"><h2 style={{ color: "var(--essentielle)" }}>Essentielles — action manuelle requise</h2></div>
      <table className="tbl">
        <thead><tr><th>Nom</th><th>IP</th><th>MAJ disponibles</th><th>Dernier check</th></tr></thead>
        <tbody>
          {list.map((v) => (
            <tr key={v.id} style={{ cursor: "default" }}>
              <td>{v.name}</td><td className="mono">{v.static_ip}</td>
              <td style={{ color: "var(--essentielle)", fontWeight: 540 }}>{v.pending} disponible(s)</td>
              <td className="muted">{v.last_check || "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </motion.div>
  );
}

function History({ rows, machines, filter, setFilter }) {
  return (
    <motion.div className="panel" variants={riseItem}>
      <div className="panel-head" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 14 }}>
        <h2>Historique</h2>
        <div style={{ display: "flex", gap: 10 }}>
          <select value={filter.vmId} onChange={(e) => setFilter((f) => ({ ...f, vmId: e.target.value }))}>
            <option value="">Toutes les machines</option>
            {machines.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
          </select>
          <select value={filter.kind} onChange={(e) => setFilter((f) => ({ ...f, kind: e.target.value }))}>
            <option value="">Tous les types</option>
            <option value="scan">Scan MAJ</option>
            <option value="sync">Resync</option>
          </select>
        </div>
      </div>
      {rows.length === 0 ? <div className="empty">Aucun événement.</div> : (
        <table className="tbl">
          <thead><tr><th>Date</th><th>Machine</th><th>Opération</th><th>Mode</th><th>Raison</th><th>Résultat</th><th>Détail</th></tr></thead>
          <tbody>
            {rows.map((e) => (
              <tr key={e.id} style={{ cursor: "default" }}>
                <td className="mono">{e.ts.replace("T", " ")}</td>
                <td>{e.vm_name}</td>
                <td><KindBadge kind={e.kind} /></td>
                <td><ModeBadge kind={e.kind} vmType={e.vm_type} /></td>
                <td><ReasonBadge reason={e.reason} detail={e.reason_detail} /></td>
                <td><StatusBadge status={e.status} /></td>
                <td className="muted">{e.reason_detail ? `${e.summary} — ${e.reason_detail}` : e.summary}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </motion.div>
  );
}
