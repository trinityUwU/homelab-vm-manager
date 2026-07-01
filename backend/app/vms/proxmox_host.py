"""Réseau des conteneurs LXC côté hôte Proxmox (net0, via `pct set`).

Un LXC n'est pas un client DHCP autonome : `pve-container` réinjecte la
config réseau de net0 dans l'invité à CHAQUE démarrage (ifupdown ou
systemd-networkd selon l'OS détecté), écrasant tout ce qu'on pose depuis
l'intérieur. La seule persistance fiable passe par net0 lui-même, changé
à chaud via `pct set` (hotplug, pas de reboot du conteneur nécessaire).
"""
from ..core.ssh_client import SSHError, SSHSession


def _parse_net0(raw: str) -> dict[str, str]:
    """Découpe une ligne net0 ("name=eth0,bridge=vmbr0,ip=dhcp,...") en dict."""
    fields: dict[str, str] = {}
    for part in raw.strip().split(","):
        if "=" in part:
            key, _, value = part.partition("=")
            fields[key] = value
    return fields


def _render_net0(fields: dict[str, str]) -> str:
    return ",".join(f"{k}={v}" for k, v in fields.items())


def get_net0(session: SSHSession, vmid: int) -> dict[str, str]:
    """Lit net0 du conteneur <vmid> sur l'hôte Proxmox (pct config)."""
    code, out, err = session.run(f"pct config {vmid}")
    if code != 0:
        raise SSHError(f"lecture config LXC {vmid} échouée : {err[:300]}")
    for line in out.splitlines():
        if line.startswith("net0:"):
            return _parse_net0(line.split(":", 1)[1])
    raise SSHError(f"aucune interface net0 déclarée sur le conteneur {vmid}")


def set_static_ip(session: SSHSession, vmid: int, static_ip: str, gateway: str) -> str:
    """Bascule net0 en IP statique via pct set (hotplug). Renvoie l'interface
    déclarée (name=), pour les logs — inutile d'aller la détecter en SSH invité."""
    fields = get_net0(session, vmid)
    fields["ip"] = f"{static_ip}/24"
    fields["gw"] = gateway
    code, _out, err = session.run(f"pct set {vmid} --net0 {_render_net0(fields)}")
    if code != 0:
        raise SSHError(f"bascule IP statique LXC {vmid} échouée : {err[:300]}")
    return fields.get("name", "eth0")


def restore_dhcp(session: SSHSession, vmid: int) -> None:
    """Remet net0 en DHCP (retrait du lab) : lève ip= et gw=."""
    fields = get_net0(session, vmid)
    fields["ip"] = "dhcp"
    fields.pop("gw", None)
    code, _out, err = session.run(f"pct set {vmid} --net0 {_render_net0(fields)}")
    if code != 0:
        raise SSHError(f"retour DHCP LXC {vmid} échoué : {err[:300]}")
