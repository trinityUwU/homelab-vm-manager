"""Vérifier & Synchroniser une VM : idempotence stricte.

Ne JAMAIS modifier ce qui est déjà correct. Chaque point renvoie soit
"OK rien à faire", soit "corrigé". Agit uniquement sur la VM passée.
"""
from ..core import store
from ..core.ssh_client import SSHError, SSHSession
from ..motd.apply import apply_motd, read_motd
from ..motd.render import render
from ..netdata.streaming import enable_streaming, is_streaming
from .models import VM, now_iso
from .network import NETPLAN_PATH
from .repository import save_vm


def _check_ip(session: SSHSession, vm: VM) -> dict:
    code, out, _err = session.run("ip -4 addr show ens18 | grep -oP 'inet \\K[0-9.]+'")
    current = out.strip()
    if code == 0 and current == vm.static_ip:
        return {"point": "IP statique", "status": "ok", "detail": f"{vm.static_ip} déjà correcte"}
    from .network import render_netplan
    config = render_netplan(vm.static_ip)
    cmd = f"mkdir -p /etc/netplan && cat > {NETPLAN_PATH} <<'EOF'\n{config}EOF\nchmod 600 {NETPLAN_PATH} && netplan apply"
    session.run(cmd, sudo=True)
    return {"point": "IP statique", "status": "corrigé", "detail": f"reconfigurée vers {vm.static_ip}"}


def _check_motd(session: SSHSession, vm: VM, settings: dict) -> dict:
    expected = render(settings["motd_template"], vm, settings["lab_name"], settings["lab_line"])
    current = read_motd(session)
    if current.strip() == expected.strip():
        return {"point": "MOTD", "status": "ok", "detail": "identique au template"}
    apply_motd(session, expected)
    return {"point": "MOTD", "status": "corrigé", "detail": "réappliqué depuis le template"}


def _check_netdata(session: SSHSession, settings: dict) -> dict:
    if is_streaming(session, settings["netdata_parent_url"]):
        return {"point": "Netdata", "status": "ok", "detail": "streame vers le parent"}
    enable_streaming(session, settings["netdata_api_key"], settings["netdata_parent_url"])
    return {"point": "Netdata", "status": "corrigé", "detail": "streaming reconfiguré et relancé"}


def sync_vm(vm: VM) -> dict:
    """Connexion + 3 vérifications idempotentes. Renvoie un rapport structuré."""
    settings = store.read_settings()
    try:
        with SSHSession(vm.static_ip, vm.ssh_user, vm.ssh_password) as session:
            report = [
                _check_ip(session, vm),
                _check_motd(session, vm, settings),
                _check_netdata(session, settings),
            ]
        vm.last_seen_online = True
        vm.last_check = now_iso()
        save_vm(vm)
        return {"ok": True, "items": report}
    except SSHError as exc:
        return {"ok": False, "error": f"Connexion impossible : {exc}", "items": []}
