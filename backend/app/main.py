"""Point d'entrée FastAPI : monte les routes, démarre le scheduler quotidien."""
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from . import ws
from .core import store
from .history.routes import router as history_router
from .motd.routes import router as motd_router
from .schedule.daily import start_scheduler, stop_scheduler
from .schedule.liveness import start_liveness, stop_liveness
from .settings.routes import router as settings_router
from .vms.routes import router as vms_router
from .vms.updates_routes import router as updates_router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    store.read_settings()  # crée settings.json au premier lancement.
    start_scheduler()
    start_liveness()
    logger.info("HomeLab VM Manager démarré")
    yield
    stop_scheduler()
    stop_liveness()


app = FastAPI(title="HomeLab VM Manager", lifespan=lifespan)

# Frontend Vite en dev (port 5173) — lab local, CORS large assumé.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(vms_router)
app.include_router(updates_router)
app.include_router(settings_router)
app.include_router(motd_router)
app.include_router(history_router)
app.include_router(ws.router)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}
