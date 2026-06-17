"""Bascule de la config réseau d'une VM Debian en IP statique via netplan.

Interface fixe `ens18` (standard Proxmox). La passerelle est déduite du /24 de
l'IP statique (ex 192.168.1.x -> 192.168.1.1), hypothèse défendable en lab.
"""
import time

from ..core.config import NET_INTERFACE
from ..core.ssh_client import SSHError, SSHSession

NETPLAN_PATH = "/etc/netplan/01-homelab.yaml"


def gateway_from_ip(static_ip: str) -> str:
    octets = static_ip.split(".")
    return ".".join(octets[:3] + ["1"])


def render_netplan(static_ip: str) -> str:
    gateway = gateway_from_ip(static_ip)
    return (
        "network:\n"
        "  version: 2\n"
        "  renderer: networkd\n"
        "  ethernets:\n"
        f"    {NET_INTERFACE}:\n"
        "      dhcp4: no\n"
        f"      addresses: [{static_ip}/24]\n"
        "      routes:\n"
        "        - to: default\n"
        f"          via: {gateway}\n"
        "      nameservers:\n"
        f"        addresses: [{gateway}, 1.1.1.1]\n"
    )


def apply_static_ip(session: SSHSession, static_ip: str) -> None:
    """Écrit le netplan statique et l'applique. Coupe le réseau en cours de route."""
    config = render_netplan(static_ip)
    write_cmd = f"mkdir -p /etc/netplan && cat > {NETPLAN_PATH} <<'EOF'\n{config}EOF\nchmod 600 {NETPLAN_PATH}"
    code, _out, err = session.run(write_cmd, sudo=True)
    if code != 0:
        raise SSHError(f"écriture netplan échouée : {err}")
    # netplan apply coupe la session DHCP : on lance et on ne dépend pas du retour.
    session.run("netplan apply", sudo=True)


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
