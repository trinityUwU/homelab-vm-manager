"""Bascule de la config réseau d'une VM Debian en IP statique.

Standard Debian : /etc/network/interfaces (ifupdown), sans dépendance netplan.
Interface fixe `ens18` (standard Proxmox). La passerelle est déduite du /24 de
l'IP statique (ex 192.168.1.x -> 192.168.1.1), hypothèse défendable en lab.
"""
import time

from ..core.config import NET_INTERFACE
from ..core.ssh_client import SSHError, SSHSession

ENI_PATH = "/etc/network/interfaces"


def gateway_from_ip(static_ip: str) -> str:
    octets = static_ip.split(".")
    return ".".join(octets[:3] + ["1"])


def render_interfaces(static_ip: str) -> str:
    gateway = gateway_from_ip(static_ip)
    return (
        "# Généré par HomeLab VM Manager\n"
        "auto lo\n"
        "iface lo inet loopback\n\n"
        f"auto {NET_INTERFACE}\n"
        f"iface {NET_INTERFACE} inet static\n"
        f"    address {static_ip}/24\n"
        f"    gateway {gateway}\n"
        f"    dns-nameservers {gateway} 1.1.1.1\n"
    )


def _restart_networking(session: SSHSession) -> None:
    """Redémarre le réseau de façon détachée : la commande rend la main avant que
    la coupure n'intervienne, sinon elle tuerait la session SSH en plein milieu.
    La déconnexion qui suit est attendue (on se reconnecte sur la nouvelle IP)."""
    inner = "systemctl restart networking 2>/dev/null || ifreload -a 2>/dev/null || (ifdown ens18; ifup ens18)"
    cmd = f"nohup bash -c 'sleep 2; {inner}' >/dev/null 2>&1 &"
    try:
        session.run(cmd, sudo=True)
    except SSHError:
        pass  # la coupure réseau est le comportement normal du switch


def apply_static_ip(session: SSHSession, static_ip: str) -> None:
    """Écrit la config statique et l'applique. Coupe la session DHCP."""
    config = render_interfaces(static_ip)
    write_cmd = f"cat > {ENI_PATH} <<'EOF'\n{config}EOF"
    code, _out, err = session.run(write_cmd, sudo=True)
    if code != 0:
        raise SSHError(f"écriture /etc/network/interfaces échouée : {err}")
    _restart_networking(session)


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
