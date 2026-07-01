"""Détection temps réel online/offline des VMs (heartbeat périodique).

Distinct du scan quotidien (`daily.py`, qui compte/applique les MAJ) : ce
scheduler ne fait qu'un ping concurrent de toutes les VMs, à haute fréquence,
pour que le Dashboard reflète un shutdown/reboot en quelques secondes au lieu
d'attendre un clic « Actualiser » ou le scan du lendemain.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger

from ..vms.status import check_liveness

_scheduler = BackgroundScheduler()
_JOB_ID = "liveness_check"
_INTERVAL_SECONDS = 5


def start_liveness() -> None:
    if not _scheduler.running:
        _scheduler.start()
    if not _scheduler.get_job(_JOB_ID):
        _scheduler.add_job(check_liveness, "interval", seconds=_INTERVAL_SECONDS, id=_JOB_ID, max_instances=1)
    logger.info(f"Détection online/offline en temps réel toutes les {_INTERVAL_SECONDS}s")


def stop_liveness() -> None:
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
