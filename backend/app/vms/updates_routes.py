"""Page Mises à jour : aperçu, machines surveillées, déclenchement manuel du scan."""
import threading

from fastapi import APIRouter

from .models import VMType
from .repository import list_vms

router = APIRouter(prefix="/api/updates", tags=["updates"])


@router.get("")
def updates_overview() -> dict:
    vms = list_vms()
    essentielles = [
        {"id": v.id, "name": v.name, "static_ip": v.static_ip, "pending": v.pending_updates, "last_check": v.last_check}
        for v in vms
        if v.vm_type == VMType.ESSENTIELLE and v.pending_updates > 0
    ]
    machines = [
        {
            "id": v.id,
            "name": v.name,
            "static_ip": v.static_ip,
            "vm_type": v.vm_type.value,
            "scan_excluded": v.scan_excluded,
            "last_check": v.last_check,
            "last_update_applied": v.last_update_applied,
            "pending": v.pending_updates,
        }
        for v in vms
    ]
    return {"essentielles": essentielles, "machines": machines}


@router.post("/run-now")
def run_now() -> dict:
    """Lance immédiatement un scan de toutes les VMs non exclues (en arrière-plan)."""
    from ..history.models import EventReason
    from ..schedule.daily import run_daily_check
    threading.Thread(target=run_daily_check, args=(EventReason.MANUAL,), daemon=True).start()
    return {"started": True}
