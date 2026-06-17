"""Configuration du Netdata parent (le host, là où tourne l'app).

Un enfant ne remonte au parent que si sa clé API est explicitement autorisée
côté parent, dans /etc/netdata/stream.conf, par une section `[<clé>]`. L'app
tournant sur le host, on écrit cette section en local (idempotent) : sans elle,
chaque VM streame dans le vide et n'apparaît jamais dans l'interface centrale.
"""
import shutil
import subprocess
from pathlib import Path

from loguru import logger

PARENT_STREAM_CONF = "/etc/netdata/stream.conf"
PARENT_CACHE_DIR = Path("/var/cache/netdata")


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


def _remove_stale(identifier: str) -> bool:
    """Retire un nœud via `netdatacli remove-stale-node` (méthode officielle, pas
    de restart). L'identifiant peut être un MACHINE_GUID, un hostname ou un node id."""
    try:
        result = subprocess.run(
            ["netdatacli", "remove-stale-node", identifier],
            capture_output=True,
            timeout=15,
            text=True,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        logger.error(f"netdatacli remove-stale-node {identifier} : {exc}")
        return False
    if result.returncode == 0:
        logger.info(f"Nœud retiré du parent Netdata : {identifier}")
        return True
    logger.warning(f"remove-stale-node {identifier} : {result.stderr.strip() or result.stdout.strip()}")
    return False


def forget_node(machine_guid: str, hostname: str = "") -> bool:
    """Retire un nœud de l'interface du parent. Priorité à `netdatacli
    remove-stale-node` (GUID puis hostname), repli sur la purge du cache + restart
    si netdatacli est absent. Idempotent, best-effort — ne bloque pas la suppression."""
    for identifier in (machine_guid, hostname):
        if identifier and _remove_stale(identifier):
            return True
    if not machine_guid:
        return False
    node_dir = PARENT_CACHE_DIR / machine_guid
    if not node_dir.is_dir():
        return False
    try:
        shutil.rmtree(node_dir)
        subprocess.run(
            ["systemctl", "restart", "netdata"],
            check=True,
            capture_output=True,
            timeout=30,
        )
        logger.info(f"Nœud purgé (cache) du parent Netdata : {machine_guid[:8]}…")
        return True
    except (OSError, subprocess.SubprocessError) as exc:
        logger.error(f"Purge du nœud {machine_guid[:8]}… échouée : {exc}")
        return False
