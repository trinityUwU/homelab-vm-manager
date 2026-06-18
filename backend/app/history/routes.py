"""Routes du journal d'événements : lecture filtrable + flux SSE temps réel."""
import asyncio
import json
import queue
from collections.abc import AsyncIterator

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from . import repository
from ..core.events import bus
from .models import EventKind

router = APIRouter(prefix="/api/history", tags=["history"])

# Heartbeat sous le timeout d'un éventuel reverse-proxy pour garder la connexion.
_HEARTBEAT_SECONDS = 25


@router.get("")
def get_history(
    vm_id: str | None = Query(default=None),
    kind: EventKind | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
) -> list[dict]:
    return repository.list_events(vm_id=vm_id, kind=kind, limit=limit)


@router.get("/stream")
async def stream() -> StreamingResponse:
    """Pousse chaque nouvel événement du journal en direct (Server-Sent Events)."""
    client = bus.subscribe()

    async def gen() -> AsyncIterator[str]:
        try:
            yield ": connecté\n\n"
            while True:
                try:
                    event = await asyncio.to_thread(client.get, True, _HEARTBEAT_SECONDS)
                    yield f"data: {json.dumps(event)}\n\n"
                except queue.Empty:
                    yield ": ping\n\n"  # maintient la connexion ouverte.
        finally:
            bus.unsubscribe(client)

    headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"}
    return StreamingResponse(gen(), media_type="text/event-stream", headers=headers)
