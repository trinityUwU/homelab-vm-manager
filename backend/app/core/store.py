"""Accès bas niveau aux fichiers JSON de stockage (VMs et settings).

Source unique de vérité pour la lecture/écriture disque. Thread-safe via un
verrou global : le scheduler et les requêtes HTTP peuvent écrire en parallèle.
"""
import json
import threading
from pathlib import Path

from loguru import logger

from .config import DATA_DIR, DEFAULT_SETTINGS, HISTORY_FILE, SETTINGS_FILE, VMS_FILE

_lock = threading.RLock()


def _read(path: Path, fallback):
    try:
        with _lock:
            if not path.exists():
                return fallback
            return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.error(f"Lecture impossible de {path}: {exc}")
        return fallback


def _write(path: Path, data) -> None:
    try:
        with _lock:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            tmp.replace(path)
    except OSError as exc:
        logger.error(f"Écriture impossible de {path}: {exc}")
        raise


def read_vms() -> list[dict]:
    return _read(VMS_FILE, [])


def write_vms(vms: list[dict]) -> None:
    _write(VMS_FILE, vms)


def read_settings() -> dict:
    data = _read(SETTINGS_FILE, None)
    if data is None:
        _write(SETTINGS_FILE, DEFAULT_SETTINGS)
        return dict(DEFAULT_SETTINGS)
    # Complète les clés manquantes si le fichier vient d'une version antérieure.
    merged = {**DEFAULT_SETTINGS, **data}
    return merged


def write_settings(settings: dict) -> None:
    _write(SETTINGS_FILE, settings)


def read_history() -> list[dict]:
    return _read(HISTORY_FILE, [])


def write_history(events: list[dict]) -> None:
    _write(HISTORY_FILE, events)
