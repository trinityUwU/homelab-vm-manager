"""Resynchronisation automatique déclenchée par une modification de config.

Quand un paramètre resyncable change (MOTD, nom/ligne du lab), les VMs concernées
sont resynchronisées en arrière-plan — l'utilisateur n'a plus à le faire à la main.
Respecte le réglage `auto_resync_on_config_change` et l'exclusion de scan par VM.
"""
import threading

from loguru import logger

from ..core import store
from ..history.models import EventReason
from .models import VM
from .repository import list_vms
from .sync import sync_vm

# Clés de settings dont la modification doit déclencher une resync.
RESYNCABLE_KEYS = frozenset({"motd_template", "lab_name", "lab_line"})


def trigger_if_relevant(changed_keys: set[str], detail: str) -> bool:
    """Lance une resync auto si une clé resyncable a changé. Renvoie True si lancée."""
    if not (changed_keys & RESYNCABLE_KEYS):
        return False
    return resync_all(detail)


def resync_all(reason_detail: str) -> bool:
    """Resync en arrière-plan les VMs provisionnées non exclues. Renvoie True si lancée."""
    if not store.read_settings().get("auto_resync_on_config_change", True):
        return False
    targets = [vm for vm in list_vms() if vm.provisioned and not vm.scan_excluded]
    if not targets:
        return False
    threading.Thread(target=_run, args=(targets, reason_detail), daemon=True).start()
    return True


def _run(targets: list[VM], reason_detail: str) -> None:
    logger.info(f"Resync auto ({reason_detail}) sur {len(targets)} VM(s)")
    for vm in targets:
        try:
            sync_vm(vm, reason=EventReason.CONFIG_CHANGE, reason_detail=reason_detail)
        except Exception as exc:  # noqa: BLE001 — best effort, ne bloque pas les autres.
            logger.warning(f"Resync auto {vm.name} : {exc}")
