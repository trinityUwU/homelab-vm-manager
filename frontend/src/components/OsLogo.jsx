// Logo réel de l'OS (simple-icons, bundlé localement — aucun CDN).
import {
  siDebian, siUbuntu, siFedora, siArchlinux, siRaspberrypi,
  siRedhat, siAlpinelinux, siOpensuse, siLinux,
} from "simple-icons";

// os_id normalisé côté backend -> icône de marque. Repli : Tux générique.
const ICONS = {
  debian: siDebian,
  ubuntu: siUbuntu,
  fedora: siFedora,
  arch: siArchlinux,
  raspberrypi: siRaspberrypi,
  rhel: siRedhat,
  alpine: siAlpinelinux,
  opensuse: siOpensuse,
};

function pick(osId) {
  if (!osId) return siLinux;
  const key = Object.keys(ICONS).find((k) => osId.startsWith(k));
  return key ? ICONS[key] : siLinux;
}

export default function OsLogo({ osId, size = 18, mono = false }) {
  const icon = pick(osId);
  return (
    <svg
      role="img"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill={mono ? "currentColor" : `#${icon.hex}`}
      style={{ flexShrink: 0 }}
      aria-label={icon.title}
    >
      <title>{icon.title}</title>
      <path d={icon.path} />
    </svg>
  );
}
