"""Routes HTTP du domaine VM."""
import threading

from fastapi import APIRouter, HTTPException

from ..core.jobs import registry
from ..core.ssh_client import test_connection
from . import repository, status
from .maintenance import APT_ACTIONS, run_apt
from .models import TestSSHRequest, VMCreate, VMUpdate
from .provisioning import run_provisioning
from .teardown import run_deletion
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


@router.post("/{vm_id}/delete")
def delete(vm_id: str) -> dict:
    if repository.get_vm(vm_id) is None:
        raise HTTPException(404, "VM introuvable")
    job = registry.create()
    threading.Thread(target=run_deletion, args=(job, vm_id), daemon=True).start()
    return {"job_id": job.id}
