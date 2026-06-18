// Badges du journal : type d'opération, mode (MAJ auto / notifié), raison, résultat.

export function KindBadge({ kind }) {
  const label = kind === "scan" ? "Scan MAJ" : "Resync";
  return <span className="badge badge-soft badge-xs">{label}</span>;
}

// Mode = comportement de MAJ. Standard applique automatiquement, Essentielle notifie.
export function ModeBadge({ kind, vmType }) {
  if (kind !== "scan") return <span className="badge badge-muted badge-xs">—</span>;
  const essentielle = vmType === "essentielle";
  return (
    <span className={`badge badge-xs ${essentielle ? "badge-essentielle" : "badge-standard"}`}>
      {essentielle ? "Notifié" : "MAJ auto"}
    </span>
  );
}

const REASON = {
  scheduled: { label: "Planifié", cls: "badge-soft" },
  config_change: { label: "Modif. config", cls: "badge-standard" },
  manual: { label: "Manuel", cls: "badge-soft" },
};

export function ReasonBadge({ reason, detail }) {
  const r = REASON[reason] || { label: reason, cls: "badge-soft" };
  return <span className={`badge badge-xs ${r.cls}`} title={detail || undefined}>{r.label}</span>;
}

const STATUS = {
  running: { label: "En cours", cls: "badge-running" },
  ok: { label: "Conforme", cls: "badge-ok" },
  changed: { label: "Appliqué", cls: "badge-ok" },
  notified: { label: "À traiter", cls: "badge-essentielle" },
  offline: { label: "Hors ligne", cls: "badge-muted" },
  error: { label: "Erreur", cls: "badge-danger" },
};

export function StatusBadge({ status }) {
  const s = STATUS[status] || { label: status, cls: "badge-soft" };
  return (
    <span className={`badge badge-xs ${s.cls}`}>
      {status === "running" && <span className="badge-pulse" />}
      {s.label}
    </span>
  );
}
