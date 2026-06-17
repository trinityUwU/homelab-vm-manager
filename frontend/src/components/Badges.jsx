// Indicateurs visuels : type de VM (bleu/orange) et statut (en ligne/hors ligne).

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
    <span className={`badge ${online ? "online" : "offline"}`}>
      <span className="dot" /> {online ? "En ligne" : "Hors ligne"}
    </span>
  );
}
