"""CRUD du domaine VM par-dessus le store JSON.

Les mots de passe transitent par le module secrets à l'entrée/sortie du disque.
"""
import uuid

from ..core import secrets, store
from .models import VM, VMCreate, VMUpdate, now_iso


def _to_storage(vm: VM) -> dict:
    data = vm.model_dump()
    data["ssh_password"] = secrets.seal(vm.ssh_password)
    return data


def _from_storage(data: dict) -> VM:
    raw = dict(data)
    raw["ssh_password"] = secrets.reveal(data.get("ssh_password", ""))
    return VM(**raw)


def list_vms() -> list[VM]:
    return [_from_storage(d) for d in store.read_vms()]


def get_vm(vm_id: str) -> VM | None:
    for data in store.read_vms():
        if data.get("id") == vm_id:
            return _from_storage(data)
    return None


def create_vm(payload: VMCreate) -> VM:
    vm = VM(id=uuid.uuid4().hex, **payload.model_dump())
    rows = store.read_vms()
    rows.append(_to_storage(vm))
    store.write_vms(rows)
    return vm


def update_vm(vm_id: str, patch: VMUpdate) -> VM | None:
    rows = store.read_vms()
    for index, data in enumerate(rows):
        if data.get("id") == vm_id:
            current = _from_storage(data)
            changes = patch.model_dump(exclude_unset=True)
            updated = current.model_copy(update=changes)
            rows[index] = _to_storage(updated)
            store.write_vms(rows)
            return updated
    return None


def save_vm(vm: VM) -> None:
    """Persiste un objet VM complet (utilisé par provisioning/sync/scheduler)."""
    rows = store.read_vms()
    for index, data in enumerate(rows):
        if data.get("id") == vm.id:
            rows[index] = _to_storage(vm)
            store.write_vms(rows)
            return
    rows.append(_to_storage(vm))
    store.write_vms(rows)


def delete_vm(vm_id: str) -> bool:
    rows = store.read_vms()
    kept = [d for d in rows if d.get("id") != vm_id]
    if len(kept) == len(rows):
        return False
    store.write_vms(kept)
    return True


def mark_provisioned(vm: VM) -> None:
    vm.provisioned = True
    vm.install_date = vm.install_date or now_iso()
    save_vm(vm)
