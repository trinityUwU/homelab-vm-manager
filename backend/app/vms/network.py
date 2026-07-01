"""Utilitaires réseau génériques côté invité (lecture seule) et attente reconnexion.

La bascule en IP statique elle-même est gérée côté hôte Proxmox (net0, voir
proxmox_host.py) — un LXC ne peut pas la faire tenir depuis l'intérieur,
Proxmox réinjecte sa propre config réseau à chaque démarrage du conteneur.
"""
import time

from ..core.config import NET_INTERFACE
from ..core.ssh_client import SSHError, SSHSession


def detect_interface(session: SSHSession) -> str:
    """Nom réel de l'interface principale de la VM (eth0 en LXC standard).

    Priorité : interface portant la route par défaut (= celle qui a l'IP active).
    Repli : première interface physique hors lo. Dernier repli : NET_INTERFACE."""
    code, out, _err = session.run(
        "ip -o -4 route show to default 2>/dev/null | awk '{print $5}' | head -1"
    )
    iface = out.strip()
    if code == 0 and iface:
        return iface
    code, out, _err = session.run(
        "ls /sys/class/net 2>/dev/null | grep -v '^lo$' | head -1"
    )
    iface = out.strip()
    return iface if iface else NET_INTERFACE


def gateway_from_ip(static_ip: str) -> str:
    octets = static_ip.split(".")
    return ".".join(octets[:3] + ["1"])


def wait_for_host(host: str, user: str, password: str, attempts: int = 12, delay: int = 5) -> None:
    """Attend que la VM réponde en SSH sur la nouvelle IP (le réseau coupe au switch)."""
    last: Exception | None = None
    for _ in range(attempts):
        time.sleep(delay)
        try:
            with SSHSession(host, user, password, timeout=8):
                return
        except SSHError as exc:
            last = exc
    raise SSHError(f"VM injoignable sur {host} après le switch réseau ({last})")
