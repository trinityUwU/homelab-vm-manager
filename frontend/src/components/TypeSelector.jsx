// Sélecteur de type de VM, visuellement bleu (Standard) ou orange (Essentielle).

export default function TypeSelector({ value, onChange }) {
  return (
    <div className="type-toggle">
      <div
        className={`type-opt ${value === "standard" ? "sel-standard" : ""}`}
        onClick={() => onChange("standard")}
      >
        <div className="name">Standard</div>
        <div className="desc">Mises à jour appliquées automatiquement</div>
      </div>
      <div
        className={`type-opt ${value === "essentielle" ? "sel-essentielle" : ""}`}
        onClick={() => onChange("essentielle")}
      >
        <div className="name">Essentielle</div>
        <div className="desc">MAJ vérifiées mais jamais appliquées seules</div>
      </div>
    </div>
  );
}
