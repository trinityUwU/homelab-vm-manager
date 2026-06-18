"""Vérification et application des mises à jour, quel que soit le gestionnaire.

Délègue les commandes réelles à `package_manager` (apt/dnf/pacman/zypper/apk),
détecté en live sur la VM. Ce module reste la logique métier « MAJ », agnostique.
"""
from ..core.ssh_client import SSHError, SSHSession
from .package_manager import PackageManager, detect


def count_pending(session: SSHSession) -> int:
    """Nombre de paquets upgradables (rafraîchit d'abord les listes)."""
    pm = detect(session)
    session.run(pm.refresh, sudo=True, timeout=pm.refresh_timeout)
    return _count(session, pm)


def count_pending_fast(session: SSHSession) -> int:
    """Compte les paquets upgradables sans rafraîchir les listes."""
    return _count(session, detect(session))


def apply_upgrades(session: SSHSession) -> None:
    """Applique toutes les mises à jour, 100% non-interactif (VM Standard)."""
    pm = detect(session)
    code, _out, err = session.run(pm.upgrade, sudo=True, timeout=pm.upgrade_timeout)
    if code != 0:
        raise SSHError(f"{pm.name} upgrade échoué : {err[:300]}")


def _count(session: SSHSession, pm: PackageManager) -> int:
    code, out, _err = session.run(pm.count)
    if code != 0:
        return 0
    try:
        return int(out.strip() or "0")
    except ValueError:
        return 0
