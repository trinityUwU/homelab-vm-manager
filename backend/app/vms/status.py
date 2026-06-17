"""Ping ICMP des VMs et rafraîchissement de leur statut online/offline."""
import subprocess

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


def refresh_vm_status(vm: VM) -> bool:
    online = ping(vm.static_ip)
    vm.last_seen_online = online
    vm.last_check = now_iso()
    save_vm(vm)
    return online


def refresh_all() -> list[VM]:
    vms = list_vms()
    for vm in vms:
        vm.last_seen_online = ping(vm.static_ip)
    for vm in vms:
        save_vm(vm)
    return vms
