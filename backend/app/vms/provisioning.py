"""Orchestration du provisioning d'une VM, étape par étape, avec logs live.

Ordre imposé : bascule net0 statique côté hôte Proxmox -> attente nouvelle IP ->
connexion -> install Netdata -> streaming -> MOTD. Si dhcp_ip est vide, la VM
est déjà en statique : on saute l'étape réseau.
"""
from loguru import logger

from ..core import store
from ..core.jobs import Job
from ..core.ssh_client import SSHError, SSHSession
from ..motd.apply import apply_motd
from ..motd.render import render
from ..netdata.parent import ensure_parent_accepts
from ..netdata.streaming import (
    enable_streaming,
    ensure_prerequisites,
    install_netdata,
    read_machine_guid,
    set_display_hostname,
)
from . import proxmox_host
from .models import VM
from .network import gateway_from_ip, wait_for_host
from .repository import mark_provisioned, save_vm


def _settings_or_raise() -> dict:
    settings = store.read_settings()
    if not settings.get("netdata_api_key"):
        raise SSHError("clé API Netdata absente — renseigne-la dans les Paramètres")
    if not settings.get("proxmox_host"):
        raise SSHError("hôte Proxmox absent — renseigne-le dans les Paramètres")
    return settings


def _switch_network(job: Job, vm: VM, settings: dict) -> SSHSession:
    job.emit("step", "Bascule en IP statique (net0, hôte Proxmox)…", 0.15, "network")
    gateway = gateway_from_ip(vm.static_ip)
    with SSHSession(
        settings["proxmox_host"], settings["proxmox_ssh_user"], settings["proxmox_ssh_password"]
    ) as host:
        iface = proxmox_host.set_static_ip(host, vm.vmid, vm.static_ip, gateway)
    job.emit("log", f"Interface déclarée (net0) : {iface}", 0.28, "network")
    job.emit("step", f"Attente de la VM sur {vm.static_ip}…", 0.35, "wait")
    wait_for_host(vm.static_ip, vm.ssh_user, vm.ssh_password)
    job.emit("step", f"Connexion sur {vm.static_ip}…", 0.45, "reconnect")
    session = SSHSession(vm.static_ip, vm.ssh_user, vm.ssh_password)
    session.connect()
    return session


def _connect_static(job: Job, vm: VM) -> SSHSession:
    job.emit("step", f"VM déjà en statique — connexion sur {vm.static_ip}…", 0.40, "ssh_static")
    session = SSHSession(vm.static_ip, vm.ssh_user, vm.ssh_password)
    session.connect()
    return session


def _install_monitoring(job: Job, session: SSHSession, vm: VM, settings: dict) -> None:
    job.emit("step", "Vérification des prérequis (wget, curl)…", 0.55, "prereqs")
    ensure_prerequisites(session)
    job.emit("step", "Installation de Netdata (kickstart.sh)…", 0.60, "netdata_install")
    install_netdata(session)
    code, real_host, _err = session.run("hostname")
    display = f"{real_host.strip()} ( HomeLab : {vm.name} )"
    set_display_hostname(session, display)
    job.emit("log", f"Nom Netdata : {display}", 0.78, "netdata_name")
    job.emit("step", "Configuration du streaming vers 192.168.1.103…", 0.80, "netdata_stream")
    enable_streaming(session, settings["netdata_api_key"], settings["netdata_parent_url"])
    vm.netdata_guid = read_machine_guid(session)


def _apply_motd(job: Job, session: SSHSession, vm: VM, settings: dict) -> None:
    job.emit("step", "Génération et application du MOTD…", 0.92, "motd")
    mark_provisioned(vm)  # fixe install_date avant le rendu.
    content = render(settings["motd_template"], vm, settings["lab_name"], settings["lab_line"])
    apply_motd(session, content)


def run_provisioning(job: Job, vm_id: str) -> None:
    """Point d'entrée exécuté dans un thread. Pousse tout le flux dans le job."""
    from .repository import get_vm

    vm = get_vm(vm_id)
    if vm is None:
        job.finish(False, "VM introuvable")
        return
    session: SSHSession | None = None
    try:
        settings = _settings_or_raise()
        job.emit("step", f"Provisioning de « {vm.name} »", 0.05, "start")
        if ensure_parent_accepts(settings["netdata_api_key"]):
            job.emit("log", "Clé API déclarée côté host Netdata (parent)", 0.07, "parent")
        session = _switch_network(job, vm, settings) if vm.dhcp_ip else _connect_static(job, vm)
        _install_monitoring(job, session, vm, settings)
        _apply_motd(job, session, vm, settings)
        vm.last_seen_online = True
        save_vm(vm)
        job.finish(True, f"VM « {vm.name} » provisionnée et connectée à Netdata")
    except SSHError as exc:
        logger.error(f"Provisioning {vm.name} échoué : {exc}")
        job.finish(False, f"Échec : {exc}")
    finally:
        if session is not None:
            session.close()
