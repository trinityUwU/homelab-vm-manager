"""Abstraction du gestionnaire de paquets selon l'OS de la VM.

Les commandes diffèrent (apt ≠ dnf ≠ pacman…). On ne se fie pas à os-release :
on détecte le binaire réellement présent sur la machine, plus fiable. Chaque
gestionnaire expose les mêmes trois capacités : rafraîchir, mettre à niveau, compter.
"""
from dataclasses import dataclass

from ..core.ssh_client import SSHError, SSHSession


@dataclass(frozen=True)
class PackageManager:
    name: str             # apt / dnf / pacman / zypper / apk
    binary: str           # binaire testé pour la détection
    refresh: str          # rafraîchir les listes de paquets (sudo)
    upgrade: str          # appliquer toutes les MAJ, 100% non-interactif (sudo)
    count: str            # compter les MAJ disponibles -> un entier sur stdout
    refresh_timeout: int = 240
    upgrade_timeout: int = 1800


# Ordre = priorité de détection. apt en premier (cible homelab Debian/Raspberry).
_MANAGERS: tuple[PackageManager, ...] = (
    PackageManager(
        name="apt", binary="apt-get",
        refresh="apt-get update",
        upgrade=('DEBIAN_FRONTEND=noninteractive apt-get -y '
                 '-o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" upgrade'),
        count="apt-get -s upgrade 2>/dev/null | grep -c '^Inst' || true",
    ),
    PackageManager(
        name="dnf", binary="dnf",
        refresh="dnf -y -q makecache",
        upgrade="dnf -y upgrade",
        count="dnf -q check-update 2>/dev/null | grep -cE '^[a-zA-Z0-9].*\\.' || true",
    ),
    PackageManager(
        name="pacman", binary="pacman",
        refresh="pacman -Sy --noconfirm",
        upgrade="pacman -Syu --noconfirm",
        count="pacman -Qu 2>/dev/null | grep -c . || true",
    ),
    PackageManager(
        name="zypper", binary="zypper",
        refresh="zypper -n refresh",
        upgrade="zypper -n update",
        count="zypper -q list-updates 2>/dev/null | grep -c '^v |' || true",
    ),
    PackageManager(
        name="apk", binary="apk",
        refresh="apk update",
        upgrade="apk upgrade",
        count="apk version -l '<' 2>/dev/null | grep -vc 'Installed:' || true",
    ),
)


def detect(session: SSHSession) -> PackageManager:
    """Renvoie le gestionnaire de paquets présent sur la VM (1 aller-retour SSH)."""
    binaries = " ".join(pm.binary for pm in _MANAGERS)
    _code, out, _err = session.run(f"command -v {binaries} 2>/dev/null | head -1")
    found = out.strip().rsplit("/", 1)[-1]
    for pm in _MANAGERS:
        if pm.binary == found:
            return pm
    raise SSHError("aucun gestionnaire de paquets reconnu (apt/dnf/pacman/zypper/apk)")
