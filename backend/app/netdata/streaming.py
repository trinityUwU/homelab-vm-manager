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


def install_netdata(session: SSHSession) -> None:
    cmd = (
        f"wget -qO /tmp/kickstart.sh {KICKSTART} && "
        "sh /tmp/kickstart.sh --dont-wait --disable-telemetry --non-interactive"
    )
    code, _out, err = session.run(cmd, sudo=True)
    if code != 0:
        raise SSHError(f"installation Netdata échouée : {err[:300]}")


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


def disable_streaming(session: SSHSession) -> None:
    """Désactive le streaming côté enfant (utilisé à la suppression de la VM)."""
    cmd = (
        f"sed -i 's/^\\s*enabled\\s*=\\s*yes/    enabled = no/' {STREAM_CONF} "
        "2>/dev/null; systemctl restart netdata 2>/dev/null || true"
    )
    session.run(cmd, sudo=True)


def is_streaming(session: SSHSession, parent: str = NETDATA_PARENT) -> bool:
    code, _out, _err = session.run("systemctl is-active --quiet netdata")
    if code != 0:
        return False
    host = parent.split(":")[0]
    grep = f"grep -qs 'destination = {host}' {STREAM_CONF} && grep -qs 'enabled = yes' {STREAM_CONF}"
    code, _out, _err = session.run(grep, sudo=True)
    return code == 0
