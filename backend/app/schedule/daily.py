"""Vérification quotidienne planifiée (APScheduler).

À l'heure configurée : ping chaque VM. Éteinte -> rien. Allumée + Standard ->
applique les MAJ. Allumée + Essentielle -> notifie seulement (compte les MAJ).
Ne supprime jamais une VM pour inactivité. Le statut online/offline temps réel
(indépendant de ce scan) est géré par `liveness.py`.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger

from ..core import store
from ..core.ssh_client import SSHError, SSHSession
from ..history import repository as history
from ..history.models import EventKind, EventReason, EventStatus
from ..vms.models import VM, VMType, now_iso
from ..vms.repository import list_vms, save_vm
from ..vms.status import ping
from ..vms.updates import apply_upgrades, count_pending

_scheduler = BackgroundScheduler()
_JOB_ID = "daily_check"


def _process_vm(vm: VM, reason: EventReason) -> None:
    event = history.record(
        kind=EventKind.SCAN,
        reason=reason,
        vm_id=vm.id,
        vm_name=vm.name,
        vm_type=vm.vm_type.value,
        status=EventStatus.RUNNING,
        summary="Vérification des mises à jour en cours…",
    )
    if not ping(vm.static_ip):
        vm.last_seen_online = False
        vm.last_check = now_iso()
        save_vm(vm)
        _finish_scan(event.id, EventStatus.OFFLINE, "VM injoignable (ping échoué)", 0, 0)
        return
    status, summary, pending, applied = _scan_online(vm)
    vm.last_check = now_iso()
    save_vm(vm)
    _finish_scan(event.id, status, summary, pending, applied)


def _scan_online(vm: VM) -> tuple[EventStatus, str, int, int]:
    """Connexion SSH + comptage/application des MAJ. Renvoie (statut, résumé, pending, applied)."""
    pending = applied = 0
    try:
        with SSHSession(vm.static_ip, vm.ssh_user, vm.ssh_password) as session:
            pending = count_pending(session)
            if vm.vm_type == VMType.STANDARD and pending > 0:
                apply_upgrades(session)
                vm.last_update_applied = now_iso()
                applied, pending = pending, 0
                status, summary = EventStatus.CHANGED, f"{applied} mise(s) à jour appliquée(s)"
            elif vm.vm_type == VMType.ESSENTIELLE and pending > 0:
                status, summary = EventStatus.NOTIFIED, f"{pending} mise(s) à jour disponible(s), non appliquées"
            else:
                status, summary = EventStatus.OK, "Système à jour, rien à faire"
            vm.pending_updates = pending
        vm.last_seen_online = True
        return status, summary, pending, applied
    except SSHError as exc:
        logger.warning(f"Check {vm.name} : {exc}")
        vm.last_seen_online = False
        return EventStatus.ERROR, f"Échec SSH : {exc}", pending, applied


def _finish_scan(event_id: str, status: EventStatus, summary: str, pending: int, applied: int) -> None:
    history.update_event(event_id, status=status, summary=summary, items=[{"pending": pending, "applied": applied}])


def run_daily_check(reason: EventReason = EventReason.SCHEDULED) -> None:
    """Scanne toutes les VMs non exclues. `reason` distingue planifié / manuel."""
    logger.info("Démarrage de la vérification des mises à jour")
    for vm in list_vms():
        if vm.scan_excluded:
            continue
        _process_vm(vm, reason)
    logger.info("Vérification terminée")


def reschedule() -> None:
    """(Ré)installe le job selon les paramètres courants."""
    settings = store.read_settings()
    if _scheduler.get_job(_JOB_ID):
        _scheduler.remove_job(_JOB_ID)
    if not settings.get("daily_check_enabled", True):
        logger.info("Vérification quotidienne désactivée")
        return
    _scheduler.add_job(
        run_daily_check,
        "cron",
        hour=settings.get("daily_check_hour", 3),
        minute=settings.get("daily_check_minute", 0),
        id=_JOB_ID,
    )
    logger.info(f"Check quotidien planifié à {settings['daily_check_hour']:02d}:{settings['daily_check_minute']:02d}")


def start_scheduler() -> None:
    if not _scheduler.running:
        _scheduler.start()
    reschedule()


def stop_scheduler() -> None:
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
