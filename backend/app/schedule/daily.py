"""Vérification quotidienne planifiée (APScheduler).

À l'heure configurée : ping chaque VM. Éteinte -> rien. Allumée + Standard ->
applique les MAJ. Allumée + Essentielle -> notifie seulement (compte les MAJ).
Ne supprime jamais une VM pour inactivité.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger

from ..core import store
from ..core.ssh_client import SSHError, SSHSession
from ..vms.models import VM, VMType, now_iso
from ..vms.repository import list_vms, save_vm
from ..vms.status import ping
from ..vms.updates import apply_upgrades, count_pending

_scheduler = BackgroundScheduler()
_JOB_ID = "daily_check"


def _process_vm(vm: VM) -> None:
    if not ping(vm.static_ip):
        vm.last_seen_online = False
        vm.last_check = now_iso()
        save_vm(vm)
        return
    try:
        with SSHSession(vm.static_ip, vm.ssh_user, vm.ssh_password) as session:
            pending = count_pending(session)
            if vm.vm_type == VMType.STANDARD and pending > 0:
                apply_upgrades(session)
                vm.last_update_applied = now_iso()
                pending = 0
            vm.pending_updates = pending
        vm.last_seen_online = True
    except SSHError as exc:
        logger.warning(f"Check quotidien {vm.name} : {exc}")
        vm.last_seen_online = False
    vm.last_check = now_iso()
    save_vm(vm)


def run_daily_check() -> None:
    logger.info("Démarrage de la vérification quotidienne")
    for vm in list_vms():
        _process_vm(vm)
    logger.info("Vérification quotidienne terminée")


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
