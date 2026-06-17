"""WebSocket de streaming des logs d'un job (provisioning).

Le job pousse ses événements dans une file thread-safe (Paramiko tourne dans un
thread). Le WebSocket draine la file et envoie chaque événement au frontend.
"""
import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .core.jobs import registry

router = APIRouter()


@router.websocket("/ws/jobs/{job_id}")
async def job_logs(websocket: WebSocket, job_id: str) -> None:
    await websocket.accept()
    job = registry.get(job_id)
    if job is None:
        await websocket.send_json({"type": "error", "message": "job introuvable"})
        await websocket.close()
        return
    try:
        while True:
            event = await asyncio.to_thread(job.events.get)
            if event.get("type") == "__end__":
                break
            await websocket.send_json(event)
        await websocket.close()
    except WebSocketDisconnect:
        pass
    finally:
        registry.drop(job_id)
