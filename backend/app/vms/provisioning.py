"""Orchestration du provisioning d'une VM, étape par étape, avec logs live.

Ordre imposé : SSH DHCP -> switch netplan statique -> attente nouvelle IP ->
reconnexion -> install Netdata -> streaming -> MOTD. Si dhcp_ip est vide, la VM
est déjà en statique : on saute les étapes réseau (2-4).
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
)
from .models import VM
from .network import apply_static_ip, wait_for_host
from .repository import mark_provisioned, save_vm


def _settings_or_raise() -> dict:
    settings = store.read_settings()
    if not settings.get("netdata_api_key"):
        raise SSHError("clé API Netdata absente — renseigne-la dans les Paramètres")
    return settings


def _switch_network(job: Job, vm: VM) -> SSHSession:
    job.emit("step", f"Connexion SSH sur l'IP DHCP {vm.dhcp_ip}…", 0.10, "ssh_dhcp")
    with SSHSession(vm.dhcp_ip, vm.ssh_user, vm.ssh_password) as dhcp:
        job.emit("step", "Bascule en IP statique…", 0.25, "network")
        iface = apply_static_ip(dhcp, vm.static_ip)
        job.emit("log", f"Interface réseau détectée : {iface}", 0.28, "network")
    job.emit("step", f"Attente de la VM sur {vm.static_ip} (le réseau coupe)…", 0.35, "wait")
    wait_for_host(vm.static_ip, vm.ssh_user, vm.ssh_password)
    job.emit("step", f"Reconnexion sur {vm.static_ip}…", 0.45, "reconnect")
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
        session = _switch_network(job, vm) if vm.dhcp_ip else _connect_static(job, vm)
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
