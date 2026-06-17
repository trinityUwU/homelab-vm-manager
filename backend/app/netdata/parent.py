"""Configuration du Netdata parent (le host, là où tourne l'app).

Un enfant ne remonte au parent que si sa clé API est explicitement autorisée
côté parent, dans /etc/netdata/stream.conf, par une section `[<clé>]`. L'app
tournant sur le host, on écrit cette section en local (idempotent) : sans elle,
chaque VM streame dans le vide et n'apparaît jamais dans l'interface centrale.
"""
import subprocess

from loguru import logger

PARENT_STREAM_CONF = "/etc/netdata/stream.conf"


def _section(api_key: str) -> str:
    return (
        f"\n[{api_key}]\n"
        "    enabled = yes\n"
        "    allow from = *\n"
        "    default memory mode = dbengine\n"
        "    health enabled by default = auto\n"
    )


def ensure_parent_accepts(api_key: str) -> bool:
    """Garantit que le parent accepte la clé API. Idempotent : ne réécrit ni ne
    redémarre Netdata si la section existe déjà. Renvoie True si une modif a eu
    lieu. Exécution locale en root (l'app tourne sur le host)."""
    if not api_key:
        return False
    try:
        with open(PARENT_STREAM_CONF, "r", encoding="utf-8") as handle:
            current = handle.read()
    except FileNotFoundError:
        current = ""
    except OSError as exc:
        logger.error(f"Lecture {PARENT_STREAM_CONF} impossible : {exc}")
        return False

    if f"[{api_key}]" in current:
        return False

    try:
        with open(PARENT_STREAM_CONF, "a", encoding="utf-8") as handle:
            handle.write(_section(api_key))
        subprocess.run(
            ["systemctl", "restart", "netdata"],
            check=True,
            capture_output=True,
            timeout=30,
        )
        logger.info(f"Clé API déclarée côté parent et Netdata redémarré : {api_key[:8]}…")
        return True
    except (OSError, subprocess.SubprocessError) as exc:
        logger.error(f"Configuration du parent Netdata échouée : {exc}")
        return False
