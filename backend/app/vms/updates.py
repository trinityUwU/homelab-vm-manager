"""Vérification et application des mises à jour APT sur une VM Debian."""
from ..core.ssh_client import SSHError, SSHSession


def count_pending(session: SSHSession) -> int:
    """Nombre de paquets upgradables (n'applique rien)."""
    session.run("apt-get update -qq", sudo=True)
    code, out, _err = session.run("apt-get -s upgrade | grep -c '^Inst' || true")
    if code != 0:
        return 0
    try:
        return int(out.strip() or "0")
    except ValueError:
        return 0


def apply_upgrades(session: SSHSession) -> None:
    """Applique tous les upgrades (VM Standard uniquement)."""
    cmd = "DEBIAN_FRONTEND=noninteractive apt-get -y upgrade"
    code, _out, err = session.run(cmd, sudo=True)
    if code != 0:
        raise SSHError(f"apt upgrade échoué : {err[:300]}")
