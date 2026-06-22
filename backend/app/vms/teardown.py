"""Démantèlement d'une machine retirée du lab : annule tout ce que le
provisioning a posé côté cible (Netdata, MOTD, conf réseau static).

Best effort par couche : une étape qui échoue ne bloque pas les suivantes,
la suppression côté app doit toujours aboutir. Le réseau est traité en
dernier car le retour DHCP coupe la session SSH.
"""
from loguru import logger

from ..core.ssh_client import SSHSession
from ..motd.apply import MOTD_PATH
from .network import detect_interface, restore_dhcp


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


def teardown_machine(session: SSHSession) -> None:
    """Annule le provisioning côté machine. Le réseau est restauré en dernier
    (il coupe la session). Chaque couche est best effort et tracée."""
    iface = detect_interface(session)
    for label, action in (("netdata", uninstall_netdata), ("motd", clear_motd)):
        try:
            action(session)
        except Exception as exc:  # noqa: BLE001 — best effort par couche.
            logger.warning(f"teardown {label} échoué : {exc}")
    try:
        restore_dhcp(session, iface)
    except Exception as exc:  # noqa: BLE001 — la coupure réseau est attendue.
        logger.warning(f"teardown réseau (retour DHCP) : {exc}")
