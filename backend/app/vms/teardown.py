"""Démantèlement d'une machine retirée du lab : annule tout ce que le
provisioning a posé côté cible (Netdata, MOTD) et remet net0 en DHCP côté
hôte Proxmox — c'est lui la source de vérité réseau pour un LXC, pas l'invité.

Best effort par couche : une étape qui échoue ne bloque pas les suivantes,
la suppression côté app doit toujours aboutir.
"""
from loguru import logger

from ..core import store
from ..core.ssh_client import SSHSession
from ..motd.apply import MOTD_PATH
from . import proxmox_host


def uninstall_netdata(session: SSHSession) -> None:
    """Désinstalle Netdata et purge ses configs (stream.conf, netdata.conf)."""
    script = (
        "systemctl stop netdata 2>/dev/null; "
        "if [ -x /usr/libexec/netdata/netdata-uninstaller.sh ]; then "
        "/usr/libexec/netdata/netdata-uninstaller.sh --yes --force "
        "2>/dev/null || true; "
        "elif command -v apt-get >/dev/null 2>&1; then "
        "DEBIAN_FRONTEND=noninteractive apt-get remove --purge -y netdata "
        "'netdata-*' 2>/dev/null || true; fi; "
        "rm -rf /etc/netdata /var/lib/netdata /var/cache/netdata /var/log/netdata"
    )
    session.run(script, sudo=True)


def clear_motd(session: SSHSession) -> None:
    """Vide le MOTD custom posé au provisioning."""
    session.run(f": > {MOTD_PATH}", sudo=True)


def teardown_machine(session: SSHSession, vmid: int) -> None:
    """Annule le provisioning côté machine, puis restaure le DHCP au niveau
    net0 (hôte Proxmox). Chaque couche est best effort et tracée."""
    for label, action in (("netdata", uninstall_netdata), ("motd", clear_motd)):
        try:
            action(session)
        except Exception as exc:  # noqa: BLE001 — best effort par couche.
            logger.warning(f"teardown {label} échoué : {exc}")
    try:
        settings = store.read_settings()
        with SSHSession(
            settings["proxmox_host"], settings["proxmox_ssh_user"], settings["proxmox_ssh_password"]
        ) as host:
            proxmox_host.restore_dhcp(host, vmid)
    except Exception as exc:  # noqa: BLE001 — best effort, la suppression doit aboutir.
        logger.warning(f"teardown réseau (retour DHCP net0) : {exc}")
