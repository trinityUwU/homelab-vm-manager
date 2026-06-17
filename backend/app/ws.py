"""Flux de logs d'un job (provisioning) en Server-Sent Events.

SSE plutôt que WebSocket : passe par le proxy /api standard, ne se coince pas
derrière un reverse-proxy, reconnexion gérée nativement par EventSource.
Le job pousse ses événements dans une file thread-safe (Paramiko tourne dans un
thread) ; on draine la file et on émet chaque événement au frontend.
"""
import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from .core.jobs import registry

router = APIRouter()


@router.get("/api/jobs/{job_id}/stream")
async def job_stream(job_id: str) -> StreamingResponse:
    async def gen():
        job = registry.get(job_id)
        if job is None:
            yield f"data: {json.dumps({'type': 'error', 'message': 'job introuvable'})}\n\n"
            return
        try:
            while True:
                event = await asyncio.to_thread(job.events.get)
                if event.get("type") == "__end__":
                    break
                yield f"data: {json.dumps(event)}\n\n"
        finally:
            registry.drop(job_id)

    headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"}
    return StreamingResponse(gen(), media_type="text/event-stream", headers=headers)
