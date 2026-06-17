"""Application et lecture du MOTD sur une VM via SSH."""
from ..core.ssh_client import SSHError, SSHSession

MOTD_PATH = "/etc/motd"


def apply_motd(session: SSHSession, content: str) -> None:
    cmd = f"cat > {MOTD_PATH} <<'EOF'\n{content}\nEOF"
    code, _out, err = session.run(cmd, sudo=True)
    if code != 0:
        raise SSHError(f"écriture MOTD échouée : {err}")


def read_motd(session: SSHSession) -> str:
    code, out, _err = session.run(f"cat {MOTD_PATH} 2>/dev/null")
    return out if code == 0 else ""
