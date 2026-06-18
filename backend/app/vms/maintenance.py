"""Actions de maintenance paquets lancées à la demande, avec sortie live.

Polyvalent : la commande réelle dépend du gestionnaire détecté sur la VM
(apt/dnf/pacman/zypper/apk). Réutilise le système de Job (flux SSE -> terminal
qui défile) et le journal d'historique pour l'état « en cours » -> « terminé / échec ».
"""
from loguru import logger

from ..core.jobs import Job
from ..core.ssh_client import SSHError, SSHSession
from ..history import repository as history
from ..history.models import EventKind, EventReason, EventStatus
from .models import VM, now_iso
from .package_manager import PackageManager, detect
from .repository import get_vm, save_vm
from .updates import count_pending_fast

# action -> (libellé, capacité du gestionnaire, statut de succès).
# « upgrade » modifie la machine -> CHANGED ; « update » rafraîchit seulement -> OK.
PKG_ACTIONS = {
    "update": ("Vérification des mises à jour", "refresh", EventStatus.OK),
    "upgrade": ("Application des mises à jour", "upgrade", EventStatus.CHANGED),
}
# Conserve l'ancien nom pour la validation de route.
APT_ACTIONS = PKG_ACTIONS


def run_apt(job: Job, vm_id: str, action: str) -> None:
    """Point d'entrée exécuté dans un thread. Diffuse la sortie et trace l'état."""
    vm = get_vm(vm_id)
    if vm is None:
        job.finish(False, "VM introuvable")
        return
    label, capability, ok_status = PKG_ACTIONS[action]
    event = history.record(
        kind=EventKind.SCAN,
        reason=EventReason.MANUAL,
        reason_detail=label,
        vm_id=vm.id,
        vm_name=vm.name,
        vm_type=vm.vm_type.value,
        status=EventStatus.RUNNING,
        summary=f"{label} — en cours…",
    )
    job.emit("step", f"{label} sur « {vm.name} »…", 0.1, action)
    try:
        _execute(job, vm, capability, label, ok_status, event.id)
    except SSHError as exc:
        logger.error(f"Maintenance {action} sur {vm.name} : {exc}")
        history.update_event(event.id, status=EventStatus.ERROR, summary=f"{label} : {exc}")
        job.finish(False, f"Échec : {exc}")


def _execute(job: Job, vm: VM, capability: str, label: str, ok_status: EventStatus, event_id: str) -> None:
    with SSHSession(vm.static_ip, vm.ssh_user, vm.ssh_password) as session:
        pm = detect(session)
        command, timeout = _command_for(pm, capability)
        job.emit("log", f"Gestionnaire détecté : {pm.name}", 0.15, "pm")
        code = session.exec_stream(command, lambda line: job.emit("log", line, 0.5, "pkg"), sudo=True, timeout=timeout)
        if code == 0:
            vm.pending_updates = count_pending_fast(session)  # indicateur de MAJ rafraîchi.
    vm.last_seen_online = True
    vm.last_check = now_iso()
    save_vm(vm)
    if code == 0:
        history.update_event(event_id, status=ok_status, summary=f"{label} — terminée")
        job.finish(True, f"{label} terminée")
    else:
        history.update_event(event_id, status=EventStatus.ERROR, summary=f"{label} : code {code}")
        job.finish(False, f"{label} échouée (code {code})")


def _command_for(pm: PackageManager, capability: str) -> tuple[str, int]:
    if capability == "upgrade":
        return pm.upgrade, pm.upgrade_timeout
    return pm.refresh, pm.refresh_timeout
