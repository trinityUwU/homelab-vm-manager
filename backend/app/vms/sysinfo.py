"""Collecte d'informations système d'une VM via SSH : OS, noyau, archi, réseau.

Lecture seule (aucune mutation). Le résultat est persisté sur la VM pour rester
affichable dans sa fiche même hors ligne (dernières valeurs connues).
"""
from ..core.ssh_client import SSHError, SSHSession
from .models import VM, now_iso
from .network import detect_interface
from .repository import save_vm

# os-release ID -> identifiant logo normalisé. Repli : l'ID brut, puis « linux ».
_OS_ALIASES = {
    "raspbian": "raspberrypi", "pop": "ubuntu", "linuxmint": "ubuntu",
    "rocky": "rhel", "almalinux": "rhel", "centos": "rhel",
}


def _parse_os_release(raw: str) -> dict[str, str]:
    data: dict[str, str] = {}
    for line in raw.splitlines():
        if "=" in line:
            key, _, value = line.partition("=")
            data[key.strip()] = value.strip().strip('"')
    return data


def collect(session: SSHSession) -> dict:
    """Lit les infos système sur la VM connectée. N'écrit rien sur la VM distante."""
    _c, os_raw, _e = session.run("cat /etc/os-release 2>/dev/null || true")
    osr = _parse_os_release(os_raw)
    _c, kernel, _e = session.run("uname -r")
    _c, arch, _e = session.run("uname -m")
    _c, model, _e = session.run("cat /proc/device-tree/model 2>/dev/null || true")
    iface = detect_interface(session)
    _c, ip, _e = session.run(f"ip -4 addr show {iface} 2>/dev/null | grep -oP 'inet \\K[0-9.]+' | head -1")
    os_id = (osr.get("ID") or "").lower()
    if "raspberry pi" in model.lower():
        os_id = "raspberrypi"
    os_id = _OS_ALIASES.get(os_id, os_id)
    return {
        "os_id": os_id or None,
        "os_name": osr.get("PRETTY_NAME") or osr.get("NAME"),
        "os_version": osr.get("VERSION_ID"),
        "kernel": kernel.strip() or None,
        "arch": arch.strip() or None,
        "net_interface": iface,
        "current_ip": ip.strip() or None,
        "sysinfo_at": now_iso(),
    }


def inspect_vm(vm: VM) -> VM:
    """Collecte et persiste les infos système. Si hors ligne, garde le dernier état."""
    try:
        with SSHSession(vm.static_ip, vm.ssh_user, vm.ssh_password, timeout=8) as session:
            info = collect(session)
        for key, value in info.items():
            setattr(vm, key, value)
        vm.last_seen_online = True
        vm.last_check = now_iso()
    except SSHError:
        vm.last_seen_online = False
    save_vm(vm)
    return vm
