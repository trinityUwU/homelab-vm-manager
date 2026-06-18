"""Persistance du journal d'événements par-dessus le store JSON.

Append-only avec plafond de rétention. Le plus récent en tête de liste.
"""
import uuid

from ..core import store
from ..core.config import HISTORY_MAX_EVENTS
from ..core.events import bus
from .models import EventKind, EventReason, EventStatus, HistoryEvent, now_iso


def record(
    *,
    kind: EventKind,
    reason: EventReason,
    vm_id: str,
    vm_name: str,
    vm_type: str,
    status: EventStatus,
    summary: str,
    items: list[dict] | None = None,
    reason_detail: str = "",
) -> HistoryEvent:
    """Crée et persiste un événement, renvoie l'objet écrit."""
    event = HistoryEvent(
        id=uuid.uuid4().hex,
        ts=now_iso(),
        kind=kind,
        reason=reason,
        reason_detail=reason_detail,
        vm_id=vm_id,
        vm_name=vm_name,
        vm_type=vm_type,
        status=status,
        summary=summary,
        items=items or [],
    )
    payload = event.model_dump()
    rows = store.read_history()
    rows.insert(0, payload)
    if len(rows) > HISTORY_MAX_EVENTS:
        rows = rows[:HISTORY_MAX_EVENTS]
    store.write_history(rows)
    bus.publish(payload)  # diffusion temps réel aux clients SSE.
    return event


def update_event(
    event_id: str,
    *,
    status: EventStatus,
    summary: str | None = None,
    items: list[dict] | None = None,
) -> dict | None:
    """Fait évoluer un événement existant (ex : « en cours » -> « terminé »).

    Réécrit l'entrée et la rediffuse sur le bus pour que le frontend la voie
    changer d'état en temps réel. Renvoie le dict mis à jour, ou None si absent.
    """
    rows = store.read_history()
    for row in rows:
        if row.get("id") == event_id:
            row["status"] = status.value
            if summary is not None:
                row["summary"] = summary
            if items is not None:
                row["items"] = items
            row["ended_ts"] = now_iso()
            store.write_history(rows)
            bus.publish(row)
            return row
    return None


def list_events(
    *,
    vm_id: str | None = None,
    kind: EventKind | None = None,
    limit: int = 200,
) -> list[dict]:
    """Liste filtrée du plus récent au plus ancien."""
    rows = store.read_history()
    if vm_id:
        rows = [r for r in rows if r.get("vm_id") == vm_id]
    if kind:
        rows = [r for r in rows if r.get("kind") == kind.value]
    return rows[:limit]
