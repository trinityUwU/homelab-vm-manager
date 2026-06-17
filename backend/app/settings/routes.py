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
    lab_name: str | None = None
    lab_line: str | None = None
    motd_template: str | None = None


@router.get("")
def get_settings() -> dict:
    return store.read_settings()


@router.put("")
def update_settings(patch: SettingsPatch) -> dict:
    current = store.read_settings()
    changes = patch.model_dump(exclude_unset=True)
    current.update(changes)
    store.write_settings(current)
    # Réarme le scheduler si l'heure/activation a changé.
    if {"daily_check_enabled", "daily_check_hour", "daily_check_minute"} & changes.keys():
        from ..schedule.daily import reschedule
        reschedule()
    return current
