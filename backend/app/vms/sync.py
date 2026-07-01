"""Vérifier & Synchroniser une VM : idempotence stricte.

Ne JAMAIS modifier ce qui est déjà correct. Chaque point renvoie soit
"OK rien à faire", soit "corrigé". Agit uniquement sur la VM passée.
"""
from ..core import store
from ..core.ssh_client import SSHError, SSHSession
from ..history import repository as history
from ..history.models import EventKind, EventReason, EventStatus
from ..motd.apply import apply_motd, read_motd
from ..motd.render import render
from ..netdata.parent import ensure_parent_accepts
from ..netdata.streaming import enable_streaming, is_streaming
from . import network, proxmox_host
from .models import MachineType, VM, now_iso
from .network import gateway_from_ip
from .repository import save_vm


def _check_ip_lxc(vm: VM, settings: dict) -> dict:
    """Vérifie/corrige net0 côté hôte Proxmox — source de vérité pour un LXC,
    pas la config interne de l'invité (voir proxmox_host.py)."""
    expected = f"{vm.static_ip}/24"
    with SSHSession(
        settings["proxmox_host"], settings["proxmox_ssh_user"], settings["proxmox_ssh_password"]
    ) as host:
        fields = proxmox_host.get_net0(host, vm.vmid)
        if fields.get("ip") == expected:
            return {"point": "IP statique", "status": "ok", "detail": f"{vm.static_ip} déjà correcte"}
        proxmox_host.set_static_ip(host, vm.vmid, vm.static_ip, gateway_from_ip(vm.static_ip))
    return {"point": "IP statique", "status": "corrigé", "detail": f"net0 reconfigurée vers {vm.static_ip}"}


def _check_ip_qemu(session: SSHSession, vm: VM) -> dict:
    """Vérifie/corrige /etc/network/interfaces côté invité (VM QEMU pure)."""
    iface = network.detect_interface(session)
    code, out, _err = session.run(f"ip -4 addr show {iface} | grep -oP 'inet \\K[0-9.]+'")
    if code == 0 and out.strip() == vm.static_ip:
        return {"point": "IP statique", "status": "ok", "detail": f"{vm.static_ip} déjà correcte"}
    config = network.render_interfaces(vm.static_ip, iface)
    session.run(f"cat > {network.ENI_PATH} <<'EOF'\n{config}EOF", sudo=True)
    network.write_resolv_conf(session, vm.static_ip)
    network.restart_networking(session, iface)
    return {"point": "IP statique", "status": "corrigé", "detail": f"reconfigurée vers {vm.static_ip}"}


def _check_motd(session: SSHSession, vm: VM, settings: dict) -> dict:
    expected = render(settings["motd_template"], vm, settings["lab_name"], settings["lab_line"])
    current = read_motd(session)
    if current.strip() == expected.strip():
        return {"point": "MOTD", "status": "ok", "detail": "identique au template"}
    apply_motd(session, expected)
    return {"point": "MOTD", "status": "corrigé", "detail": "réappliqué depuis le template"}


def _check_netdata(session: SSHSession, settings: dict) -> dict:
    ensure_parent_accepts(settings["netdata_api_key"])
    if is_streaming(session, settings["netdata_parent_url"]):
        return {"point": "Netdata", "status": "ok", "detail": "streame vers le parent"}
    enable_streaming(session, settings["netdata_api_key"], settings["netdata_parent_url"])
    return {"point": "Netdata", "status": "corrigé", "detail": "streaming reconfiguré et relancé"}


def _summarize(report: list[dict]) -> tuple[EventStatus, str]:
    """Déduit statut + résumé lisible à partir des points du rapport."""
    corriges = [r["point"] for r in report if r["status"] == "corrigé"]
    if corriges:
        return EventStatus.CHANGED, "Corrigé : " + ", ".join(corriges)
    return EventStatus.OK, "Déjà conforme (IP, MOTD, Netdata)"


def _run_checks(vm: VM, settings: dict) -> list[dict]:
    """LXC vérifie net0 avant même la session invité (source de vérité côté
    hôte) ; QEMU vérifie l'IP dans la même session que MOTD/Netdata."""
    if vm.machine_type == MachineType.LXC:
        ip_point = _check_ip_lxc(vm, settings)
        with SSHSession(vm.static_ip, vm.ssh_user, vm.ssh_password) as session:
            return [ip_point, _check_motd(session, vm, settings), _check_netdata(session, settings)]
    with SSHSession(vm.static_ip, vm.ssh_user, vm.ssh_password) as session:
        return [
            _check_ip_qemu(session, vm),
            _check_motd(session, vm, settings),
            _check_netdata(session, settings),
        ]


def sync_vm(
    vm: VM,
    reason: EventReason = EventReason.MANUAL,
    reason_detail: str = "",
) -> dict:
    """Connexion + 3 vérifications idempotentes. Journalise (en cours -> fini) et renvoie un rapport."""
    settings = store.read_settings()
    event = history.record(
        kind=EventKind.SYNC,
        reason=reason,
        reason_detail=reason_detail,
        vm_id=vm.id,
        vm_name=vm.name,
        vm_type=vm.vm_type.value,
        status=EventStatus.RUNNING,
        summary="Vérification & synchronisation en cours…",
    )
    try:
        report = _run_checks(vm, settings)
        vm.last_seen_online = True
        vm.last_check = now_iso()
        save_vm(vm)
        status, summary = _summarize(report)
        history.update_event(event.id, status=status, summary=summary, items=report)
        return {"ok": True, "items": report}
    except SSHError as exc:
        summary = f"Connexion impossible : {exc}"
        history.update_event(event.id, status=EventStatus.OFFLINE, summary=summary, items=[])
        return {"ok": False, "error": summary, "items": []}
