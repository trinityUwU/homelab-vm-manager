"""Schémas du journal d'événements (scan & resynchronisation).

Un événement trace QUI (VM), QUOI (scan de MAJ ou sync), POURQUOI (planifié,
modification de config, manuel) et le RÉSULTAT. Le frontend en déduit les badges.
"""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class EventKind(str, Enum):
    SCAN = "scan"  # Vérification des MAJ APT (applique ou notifie selon le type VM).
    SYNC = "sync"  # Réconciliation idempotente IP / MOTD / Netdata.


class EventReason(str, Enum):
    SCHEDULED = "scheduled"          # Déclenché par le planificateur quotidien.
    CONFIG_CHANGE = "config_change"  # Déclenché par une modification dans l'application.
    MANUAL = "manual"                # Déclenché à la main depuis l'interface.


class EventStatus(str, Enum):
    RUNNING = "running"  # Action en cours (accompagnement : l'utilisateur voit que ça tourne).
    OK = "ok"            # Tout était déjà conforme, rien à faire.
    CHANGED = "changed"  # Une correction / MAJ a été appliquée.
    NOTIFIED = "notified"  # MAJ disponibles, non appliquées (VM Essentielle).
    OFFLINE = "offline"  # VM injoignable.
    ERROR = "error"      # Échec pendant l'opération.


class HistoryEvent(BaseModel):
    id: str
    ts: str
    kind: EventKind
    reason: EventReason
    reason_detail: str = ""        # Ex : « Template MOTD modifié ».
    vm_id: str
    vm_name: str
    vm_type: str                   # standard / essentielle — sert le badge de mode.
    status: EventStatus
    summary: str                   # Phrase courte lisible.
    items: list[dict] = Field(default_factory=list)  # Détail (rapport sync ou {pending, applied}).
    ended_ts: str | None = None    # Horodatage de fin (rempli quand on quitte l'état « en cours »).


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")
