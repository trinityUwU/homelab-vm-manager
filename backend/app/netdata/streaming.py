"""Configuration du streaming Netdata côté enfant (chaque VM).

Netdata n'a pas d'API REST pour enrôler un nœud : tout passe par stream.conf.
La clé API est générée une fois manuellement sur le parent (192.168.1.103),
saisie dans les Paramètres, puis réutilisée pour chaque VM. "Supprimer" un nœud
= désactiver le streaming ici ; le parent garde l'historique (nœud éphémère).
"""
from ..core.config import NETDATA_PARENT
from ..core.ssh_client import SSHError, SSHSession

STREAM_CONF = "/etc/netdata/stream.conf"
KICKSTART = "https://my-netdata.io/kickstart.sh"


def ensure_prerequisites(session: SSHSession) -> None:
    """Installe les outils requis par le kickstart Netdata s'ils manquent (idempotent)."""
    cmd = (
        "command -v wget >/dev/null 2>&1 && command -v curl >/dev/null 2>&1 "
        "|| (apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y wget curl ca-certificates)"
    )
    code, _out, err = session.run(cmd, sudo=True)
    if code != 0:
        raise SSHError(f"installation des prérequis échouée : {err[:300]}")


def install_netdata(session: SSHSession) -> None:
    cmd = (
        f"wget -qO /tmp/kickstart.sh {KICKSTART} && "
        "sh /tmp/kickstart.sh --dont-wait --disable-telemetry --non-interactive"
    )
    code, _out, err = session.run(cmd, sudo=True)
    if code != 0:
        raise SSHError(f"installation Netdata échouée : {err[:300]}")


GUID_FILE = "/var/lib/netdata/registry/netdata.public.unique.id"


NETDATA_CONF = "/etc/netdata/netdata.conf"


def set_display_hostname(session: SSHSession, display_name: str) -> None:
    """Force le nom affiché du nœud côté parent via [global] hostname du
    netdata.conf de l'enfant. Crée la section/clé si absente, la remplace sinon.
    Sans restart ici : enable_streaming relance Netdata juste après."""
    safe = display_name.replace("|", "/")
    script = (
        f'conf="{NETDATA_CONF}"; name="{safe}"; '
        'if grep -q "^\\s*\\[global\\]" "$conf" 2>/dev/null; then '
        'if grep -q "^\\s*hostname\\s*=" "$conf"; then '
        'sed -i "s|^\\s*hostname\\s*=.*|    hostname = $name|" "$conf"; '
        'else sed -i "/^\\s*\\[global\\]/a\\    hostname = $name" "$conf"; fi; '
        'else printf "[global]\\n    hostname = %s\\n" "$name" >> "$conf"; fi'
    )
    code, _out, err = session.run(script, sudo=True)
    if code != 0:
        raise SSHError(f"définition du hostname Netdata échouée : {err[:200]}")


def read_machine_guid(session: SSHSession) -> str | None:
    """Lit le MACHINE_GUID de l'enfant : c'est la clé sous laquelle le parent
    range ses données. Indispensable pour le purger du parent à la suppression."""
    code, out, _err = session.run(f"cat {GUID_FILE} 2>/dev/null")
    guid = out.strip()
    return guid if code == 0 and guid else None


def _stream_block(api_key: str, parent: str) -> str:
    return (
        "[stream]\n"
        "    enabled = yes\n"
        f"    destination = {parent}\n"
        f"    api key = {api_key}\n"
    )


def enable_streaming(session: SSHSession, api_key: str, parent: str = NETDATA_PARENT) -> None:
    block = _stream_block(api_key, parent)
    cmd = f"cat > {STREAM_CONF} <<'EOF'\n{block}EOF\nsystemctl restart netdata"
    code, _out, err = session.run(cmd, sudo=True)
    if code != 0:
        raise SSHError(f"configuration streaming échouée : {err}")


def is_streaming(session: SSHSession, parent: str = NETDATA_PARENT) -> bool:
    code, _out, _err = session.run("systemctl is-active --quiet netdata")
    if code != 0:
        return False
    host = parent.split(":")[0]
    grep = f"grep -qs 'destination = {host}' {STREAM_CONF} && grep -qs 'enabled = yes' {STREAM_CONF}"
    code, _out, _err = session.run(grep, sudo=True)
    return code == 0
