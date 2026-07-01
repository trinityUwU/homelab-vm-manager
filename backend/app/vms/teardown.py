"""Démantèlement d'une machine retirée du lab : annule tout ce que le
provisioning a posé côté cible (Netdata, MOTD) et remet net0 en DHCP côté
hôte Proxmox — c'est lui la source de vérité réseau pour un LXC, pas l'invité.

Best effort par couche : une étape qui échoue ne bloque pas les suivantes,
la suppression côté app doit toujours aboutir.
"""
from loguru import logger

from ..core import store
from ..core.jobs import Job
from ..core.ssh_client import SSHSession
from ..motd.apply import MOTD_PATH
from ..netdata.parent import forget_node
from ..netdata.streaming import read_machine_guid
from . import proxmox_host, status


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


def _teardown_guest(job: Job, vm) -> None:
    """Netdata + MOTD côté invité. Best effort : la suppression doit aboutir
    même si la machine coupe la connexion en cours de route."""
    try:
        with SSHSession(vm.static_ip, vm.ssh_user, vm.ssh_password, timeout=8) as session:
            if not vm.netdata_guid:
                vm.netdata_guid = read_machine_guid(session)
            job.emit("step", "Désinstallation de Netdata…", 0.35, "netdata")
            uninstall_netdata(session)
            job.emit("step", "Purge du MOTD…", 0.55, "motd")
            clear_motd(session)
    except Exception as exc:  # noqa: BLE001 — best effort, la suppression doit aboutir.
        logger.warning(f"teardown invité échoué : {exc}")


def _restore_host_dhcp(vmid: int) -> None:
    """Repasse net0 en DHCP côté hôte Proxmox. Best effort, même logique."""
    try:
        settings = store.read_settings()
        with SSHSession(
            settings["proxmox_host"], settings["proxmox_ssh_user"], settings["proxmox_ssh_password"]
        ) as host:
            proxmox_host.restore_dhcp(host, vmid)
    except Exception as exc:  # noqa: BLE001 — best effort, la suppression doit aboutir.
        logger.warning(f"retour DHCP net0 échoué : {exc}")


def run_deletion(job: Job, vm_id: str) -> None:
    """Point d'entrée exécuté dans un thread : démantèle puis retire l'enregistrement,
    en poussant chaque étape dans le job pour une barre de progression réelle côté UI."""
    from .repository import delete_vm, get_vm

    vm = get_vm(vm_id)
    if vm is None:
        job.finish(False, "VM introuvable")
        return

    job.emit("step", f"Suppression de « {vm.name} »", 0.05, "start")
    online = status.ping(vm.static_ip)
    if online:
        job.emit("step", f"Connexion à {vm.static_ip}…", 0.15, "connect")
        _teardown_guest(job, vm)
        job.emit("step", "Retour en DHCP (net0, hôte Proxmox)…", 0.70, "network")
        _restore_host_dhcp(vm.vmid)
    else:
        job.emit("log", "Machine hors ligne — étapes distantes ignorées", 0.5, "offline")

    job.emit("step", "Retrait du nœud Netdata parent…", 0.85, "parent")
    forget_node(vm.netdata_guid or "", vm.name)
    job.emit("step", "Suppression de l'enregistrement…", 0.95, "record")
    delete_vm(vm_id)
    state = "en ligne" if online else "hors ligne"
    job.finish(True, f"VM « {vm.name} » ({state}) supprimée")
