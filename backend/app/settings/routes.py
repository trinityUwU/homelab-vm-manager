"""Routes des paramètres globaux."""
from fastapi import APIRouter
from pydantic import BaseModel

from ..core import store

router = APIRouter(prefix="/api/settings", tags=["settings"])


class SettingsPatch(BaseModel):
    ssh_user: str | None = None
    ssh_password: str | None = None
    netdata_parent_url: str | None = None
    netdata_api_key: str | None = None
    daily_check_enabled: bool | None = None
    daily_check_hour: int | None = None
    daily_check_minute: int | None = None
    auto_resync_on_config_change: bool | None = None
    notifications_enabled: bool | None = None
    lab_name: str | None = None
    lab_line: str | None = None
    motd_template: str | None = None


# Libellés lisibles des clés resyncables, pour le détail de raison dans l'historique.
_RESYNC_LABELS = {"motd_template": "Template MOTD", "lab_name": "Nom du lab", "lab_line": "Ligne du lab"}


@router.get("")
def get_settings() -> dict:
    return store.read_settings()


@router.put("")
def update_settings(patch: SettingsPatch) -> dict:
    current = store.read_settings()
    changes = patch.model_dump(exclude_unset=True)
    # Ne retient que les clés réellement modifiées (valeur différente).
    effective = {k: v for k, v in changes.items() if current.get(k) != v}
    current.update(changes)
    store.write_settings(current)
    # Réarme le scheduler si l'heure/activation a changé.
    if {"daily_check_enabled", "daily_check_hour", "daily_check_minute"} & effective.keys():
        from ..schedule.daily import reschedule
        reschedule()
    # Resync auto si un paramètre resyncable a changé.
    from ..vms.auto_sync import trigger_if_relevant
    labels = [_RESYNC_LABELS[k] for k in effective if k in _RESYNC_LABELS]
    if labels:
        trigger_if_relevant(set(effective.keys()), " + ".join(labels) + " modifié(s)")
    return current
