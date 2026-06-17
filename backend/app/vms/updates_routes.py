"""Page Mises à jour : VMs Essentielles à notifier, VMs Standard et leur dernière MAJ."""
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
    standard = [
        {"id": v.id, "name": v.name, "static_ip": v.static_ip, "last_update_applied": v.last_update_applied}
        for v in vms
        if v.vm_type == VMType.STANDARD
    ]
    return {"essentielles": essentielles, "standard": standard}
