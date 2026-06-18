"""Routes HTTP du domaine VM."""
import threading

from fastapi import APIRouter, HTTPException

from ..core.jobs import registry
from ..core.ssh_client import SSHSession, test_connection
from ..netdata.parent import forget_node
from ..netdata.streaming import disable_streaming, read_machine_guid
from . import repository, status
from .maintenance import APT_ACTIONS, run_apt
from .models import TestSSHRequest, VMCreate, VMUpdate
from .provisioning import run_provisioning
from .sync import sync_vm
from .sysinfo import inspect_vm

router = APIRouter(prefix="/api/vms", tags=["vms"])


@router.get("")
def get_all() -> list[dict]:
    return [vm.model_dump() for vm in repository.list_vms()]


@router.post("/refresh")
def refresh_all() -> list[dict]:
    return [vm.model_dump() for vm in status.refresh_all()]


@router.post("/test-ssh")
def test_ssh(payload: TestSSHRequest) -> dict:
    ok, message = test_connection(payload.host, payload.ssh_user, payload.ssh_password)
    return {"ok": ok, "message": message}


@router.post("", status_code=201)
def create(payload: VMCreate) -> dict:
    vm = repository.create_vm(payload)
    return vm.model_dump()


@router.get("/{vm_id}")
def get_one(vm_id: str) -> dict:
    vm = repository.get_vm(vm_id)
    if vm is None:
        raise HTTPException(404, "VM introuvable")
    return vm.model_dump()


@router.put("/{vm_id}")
def update(vm_id: str, patch: VMUpdate) -> dict:
    vm = repository.update_vm(vm_id, patch)
    if vm is None:
        raise HTTPException(404, "VM introuvable")
    return vm.model_dump()


@router.get("/{vm_id}/refresh")
def refresh_one(vm_id: str) -> dict:
    vm = repository.get_vm(vm_id)
    if vm is None:
        raise HTTPException(404, "VM introuvable")
    status.refresh_vm_status(vm)
    return repository.get_vm(vm_id).model_dump()


@router.post("/{vm_id}/provision")
def provision(vm_id: str) -> dict:
    vm = repository.get_vm(vm_id)
    if vm is None:
        raise HTTPException(404, "VM introuvable")
    job = registry.create()
    threading.Thread(target=run_provisioning, args=(job, vm_id), daemon=True).start()
    return {"job_id": job.id}


@router.post("/{vm_id}/inspect")
def inspect(vm_id: str) -> dict:
    vm = repository.get_vm(vm_id)
    if vm is None:
        raise HTTPException(404, "VM introuvable")
    return inspect_vm(vm).model_dump()


@router.post("/{vm_id}/apt/{action}")
def apt_action(vm_id: str, action: str) -> dict:
    if action not in APT_ACTIONS:
        raise HTTPException(400, f"action inconnue : {action}")
    if repository.get_vm(vm_id) is None:
        raise HTTPException(404, "VM introuvable")
    job = registry.create()
    threading.Thread(target=run_apt, args=(job, vm_id, action), daemon=True).start()
    return {"job_id": job.id}


@router.post("/{vm_id}/sync")
def sync(vm_id: str) -> dict:
    vm = repository.get_vm(vm_id)
    if vm is None:
        raise HTTPException(404, "VM introuvable")
    return sync_vm(vm)


@router.delete("/{vm_id}")
def delete(vm_id: str) -> dict:
    vm = repository.get_vm(vm_id)
    if vm is None:
        raise HTTPException(404, "VM introuvable")
    online = status.ping(vm.static_ip)
    if online:
        _try_disable_streaming(vm)
    forget_node(vm.netdata_guid or "", vm.name)  # retire le nœud de l'interface du parent.
    repository.delete_vm(vm_id)
    state = "en ligne" if online else "hors ligne"
    return {"ok": True, "was_online": online, "message": f"VM « {vm.name} » ({state}) supprimée"}


def _try_disable_streaming(vm) -> None:
    """Coupe le streaming côté enfant et récupère son GUID s'il manque encore
    (VM provisionnée avant le suivi du GUID), pour pouvoir le purger du parent."""
    try:
        with SSHSession(vm.static_ip, vm.ssh_user, vm.ssh_password, timeout=8) as session:
            if not vm.netdata_guid:
                vm.netdata_guid = read_machine_guid(session)
            disable_streaming(session)
    except Exception:  # noqa: BLE001 — best effort, la suppression doit aboutir.
        pass
