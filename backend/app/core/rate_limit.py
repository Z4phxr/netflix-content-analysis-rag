import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict

from fastapi import HTTPException, Request


class InMemoryRateLimiter:
    """Simple fixed-window limiter keyed by route and client address."""

    def __init__(self) -> None:
        self._events: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def enforce(self, request: Request, route_key: str, max_per_minute: int) -> None:
        if max_per_minute <= 0:
            return

        now = time.time()
        window_start = now - 60.0
        client = request.client.host if request.client else "unknown"
        key = f"{route_key}:{client}"

        with self._lock:
            bucket = self._events[key]
            while bucket and bucket[0] < window_start:
                bucket.popleft()

            if len(bucket) >= max_per_minute:
                raise HTTPException(status_code=429, detail="Rate limit exceeded")

            bucket.append(now)


rate_limiter = InMemoryRateLimiter()
