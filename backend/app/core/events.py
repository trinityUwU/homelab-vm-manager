"""Bus d'événements en mémoire : pont thread -> async pour le temps réel.

Les producteurs (scheduler, sync, resync — tous dans des threads) publient un
événement ; chaque client SSE connecté possède sa propre file et le reçoit en
direct. Aucune connaissance métier ici : on diffuse des dicts bruts.
"""
import queue
import threading

# Au-delà de cette taille, un client trop lent perd les événements les plus anciens
# plutôt que de bloquer tout le bus.
_CLIENT_BUFFER = 200


class EventBus:
    def __init__(self) -> None:
        self._subscribers: set[queue.Queue] = set()
        self._lock = threading.Lock()

    def subscribe(self) -> "queue.Queue[dict]":
        q: queue.Queue = queue.Queue(maxsize=_CLIENT_BUFFER)
        with self._lock:
            self._subscribers.add(q)
        return q

    def unsubscribe(self, q: "queue.Queue[dict]") -> None:
        with self._lock:
            self._subscribers.discard(q)

    def publish(self, event: dict) -> None:
        with self._lock:
            subscribers = list(self._subscribers)
        for q in subscribers:
            try:
                q.put_nowait(event)
            except queue.Full:
                pass  # client lent : on saute, le temps réel n'attend personne.


bus = EventBus()
