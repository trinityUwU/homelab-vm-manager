"""Registre de jobs longue durée (provisioning, sync) avec flux de logs live.

Chaque job possède une file d'événements thread-safe. Le provisioning tourne
dans un thread (Paramiko est bloquant) et y pousse ses logs ; le WebSocket la
draine pour alimenter le terminal qui défile côté frontend.
"""
import queue
import threading
import uuid
from dataclasses import dataclass, field

_SENTINEL = {"type": "__end__"}


@dataclass
class Job:
    id: str
    events: "queue.Queue[dict]" = field(default_factory=queue.Queue)
    done: bool = False

    def emit(self, type_: str, message: str, progress: float | None = None, step: str | None = None) -> None:
        self.events.put({"type": type_, "message": message, "progress": progress, "step": step})

    def finish(self, success: bool, message: str) -> None:
        self.events.put({"type": "result", "success": success, "message": message, "progress": 1.0})
        self.events.put(dict(_SENTINEL))
        self.done = True


class JobRegistry:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def create(self) -> Job:
        job = Job(id=uuid.uuid4().hex)
        with self._lock:
            self._jobs[job.id] = job
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def drop(self, job_id: str) -> None:
        with self._lock:
            self._jobs.pop(job_id, None)


registry = JobRegistry()
