// Horodatage ISO -> libellé relatif lisible (« il y a 3 min »).

const MINUTE = 60;
const HOUR = 3600;
const DAY = 86400;

export function relativeTime(iso) {
  if (!iso) return "—";
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "—";
  const diff = Math.max(0, Math.floor((Date.now() - then) / 1000));
  if (diff < MINUTE) return "à l'instant";
  if (diff < HOUR) return `il y a ${Math.floor(diff / MINUTE)} min`;
  if (diff < DAY) return `il y a ${Math.floor(diff / HOUR)} h`;
  if (diff < 7 * DAY) return `il y a ${Math.floor(diff / DAY)} j`;
  return new Date(iso).toLocaleDateString("fr-FR", { day: "2-digit", month: "short" });
}
