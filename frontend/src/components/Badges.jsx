// Badges sémantiques : type de VM (bleu/orange) et statut (online pulsé / offline neutre).

export function TypeBadge({ type }) {
  const essentielle = type === "essentielle";
  return (
    <span className={`badge ${essentielle ? "badge-essentielle" : "badge-standard"}`}>
      {essentielle ? "Essentielle" : "Standard"}
    </span>
  );
}

export function StatusBadge({ online }) {
  return (
    <span className={`status ${online ? "online" : "offline"}`}>
      <span className={`dot ${online ? "online" : "offline"}`} />
      {online ? "En ligne" : "Hors ligne"}
    </span>
  );
}
