"""Ping ICMP des VMs et rafraîchissement de leur statut online/offline."""
import subprocess
from concurrent.futures import ThreadPoolExecutor

from ..core.events import bus
from .models import VM, now_iso
from .repository import list_vms, save_vm


def ping(host: str) -> bool:
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "2", host],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, OSError):
        return False


def _ping_all(vms: list[VM]) -> list[bool]:
    if not vms:
        return []
    with ThreadPoolExecutor(max_workers=len(vms)) as pool:
        return list(pool.map(lambda vm: ping(vm.static_ip), vms))


def refresh_vm_status(vm: VM) -> bool:
    online = ping(vm.static_ip)
    vm.last_seen_online = online
    vm.last_check = now_iso()
    save_vm(vm)
    return online


def refresh_all() -> list[VM]:
    vms = list_vms()
    for vm, online in zip(vms, _ping_all(vms)):
        vm.last_seen_online = online
        vm.last_check = now_iso()
        save_vm(vm)
    return vms


def check_liveness() -> None:
    """Ping périodique haute fréquence (heartbeat) : ne persiste et ne diffuse

    sur le bus que les VMs dont l'état online/offline vient de changer, pour
    que le Dashboard reflète un shutdown/reboot en quelques secondes sans
    attendre un clic « Actualiser » ni le scan quotidien.
    """
    vms = list_vms()
    for vm, online in zip(vms, _ping_all(vms)):
        if online == vm.last_seen_online:
            continue
        vm.last_seen_online = online
        vm.last_check = now_iso()
        save_vm(vm)
        bus.publish({
            "type": "vm_status",
            "vm_id": vm.id,
            "vm_name": vm.name,
            "online": online,
            "ts": vm.last_check,
        })
