"""Bascule de la config réseau d'une VM Debian en IP statique.

Standard Debian : /etc/network/interfaces (ifupdown), sans dépendance netplan.
Le nom de l'interface n'est PAS supposé (ens18 vs eth0 selon la VM) : il est
détecté en live sur la VM avant d'écrire. La passerelle est déduite du /24 de
l'IP statique (ex 192.168.1.x -> 192.168.1.1), hypothèse défendable en lab.
"""
import time

from ..core.config import NET_INTERFACE
from ..core.ssh_client import SSHError, SSHSession

ENI_PATH = "/etc/network/interfaces"


def detect_interface(session: SSHSession) -> str:
    """Nom réel de l'interface principale de la VM (eth0, ens18, enp0s3…).

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


def render_interfaces(static_ip: str, iface: str) -> str:
    gateway = gateway_from_ip(static_ip)
    return (
        "# Généré par HomeLab VM Manager\n"
        "auto lo\n"
        "iface lo inet loopback\n\n"
        f"auto {iface}\n"
        f"iface {iface} inet static\n"
        f"    address {static_ip}/24\n"
        f"    gateway {gateway}\n"
        f"    dns-nameservers {gateway} 1.1.1.1\n"
    )


def harden_static_persistence(session: SSHSession, iface: str) -> None:
    """Empêche le retour en DHCP au reboot : neutralise les couches qui
    reprennent la main au boot et écraseraient /etc/network/interfaces.
    Best effort multi-cause (cloud-init, NetworkManager, interfaces.d résiduel)."""
    script = (
        # cloud-init : désactive sa génération réseau + purge ses fichiers.
        'if command -v cloud-init >/dev/null 2>&1; then '
        'mkdir -p /etc/cloud/cloud.cfg.d; '
        'printf "network: {config: disabled}\\n" '
        '> /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg; '
        'rm -f /etc/netplan/50-cloud-init.yaml '
        '/etc/network/interfaces.d/50-cloud-init '
        '/etc/network/interfaces.d/50-cloud-init.cfg; fi; '
        # interfaces.d résiduel : retire toute déclaration DHCP de l'iface.
        f'rm -f /etc/network/interfaces.d/*{iface}* 2>/dev/null; '
        # NetworkManager actif : marque l'iface non gérée (ifupdown reprend).
        'if systemctl is-active --quiet NetworkManager 2>/dev/null; then '
        'mkdir -p /etc/NetworkManager/conf.d; '
        f'printf "[keyfile]\\nunmanaged-devices=interface-name:{iface}\\n" '
        '> /etc/NetworkManager/conf.d/99-homelab-unmanaged.conf; '
        'nmcli connection reload 2>/dev/null || true; fi; '
        # systemd-networkd actif : masque (ifupdown est notre source de vérité).
        'systemctl is-enabled --quiet systemd-networkd 2>/dev/null '
        '&& systemctl disable --now systemd-networkd 2>/dev/null || true'
    )
    session.run(script, sudo=True)


def _restart_networking(session: SSHSession, iface: str) -> None:
    """Redémarre le réseau de façon détachée : la commande rend la main avant que
    la coupure n'intervienne, sinon elle tuerait la session SSH en plein milieu.
    La déconnexion qui suit est attendue (on se reconnecte sur la nouvelle IP).
    `ifdown`/`ifup` ciblent l'interface réellement détectée, pas une supposée."""
    inner = (
        "systemctl restart networking 2>/dev/null || ifreload -a 2>/dev/null "
        f"|| (ifdown {iface} 2>/dev/null; ifup {iface})"
    )
    cmd = f"nohup bash -c 'sleep 2; {inner}' >/dev/null 2>&1 &"
    try:
        session.run(cmd, sudo=True)
    except SSHError:
        pass  # la coupure réseau est le comportement normal du switch


def _write_resolv_conf(session: SSHSession, static_ip: str) -> None:
    """Écrit /etc/resolv.conf directement : sur Debian minimale (sans resolvconf),
    la directive dns-nameservers est ignorée et la résolution DNS casse sinon."""
    gateway = gateway_from_ip(static_ip)
    content = f"nameserver {gateway}\nnameserver 1.1.1.1\n"
    session.run(f"cat > /etc/resolv.conf <<'EOF'\n{content}EOF", sudo=True)


def apply_static_ip(session: SSHSession, static_ip: str) -> str:
    """Détecte l'interface, écrit la config statique et l'applique. Coupe la
    session DHCP. Renvoie le nom de l'interface détectée (pour les logs)."""
    iface = detect_interface(session)
    config = render_interfaces(static_ip, iface)
    write_cmd = f"cat > {ENI_PATH} <<'EOF'\n{config}EOF"
    code, _out, err = session.run(write_cmd, sudo=True)
    if code != 0:
        raise SSHError(f"écriture /etc/network/interfaces échouée : {err}")
    _write_resolv_conf(session, static_ip)
    harden_static_persistence(session, iface)
    _restart_networking(session, iface)
    return iface


def render_interfaces_dhcp(iface: str) -> str:
    return (
        "# Restauré par HomeLab VM Manager (retrait du lab)\n"
        "auto lo\n"
        "iface lo inet loopback\n\n"
        f"auto {iface}\n"
        f"iface {iface} inet dhcp\n"
    )


def restore_dhcp(session: SSHSession, iface: str) -> None:
    """Remet l'interface en DHCP et lève le verrou cloud-init posé au provisioning.
    Détaché : le réseau coupe (la machine quitte le lab), la coupure est attendue."""
    config = render_interfaces_dhcp(iface)
    write_cmd = (
        f"cat > {ENI_PATH} <<'EOF'\n{config}EOF\n"
        "rm -f /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg "
        "/etc/NetworkManager/conf.d/99-homelab-unmanaged.conf 2>/dev/null; "
        "rm -f /etc/resolv.conf 2>/dev/null"
    )
    session.run(write_cmd, sudo=True)
    _restart_networking(session, iface)


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
