import asyncio
import time
from collections import defaultdict, deque
from fastapi import HTTPException


class SlidingWindowLimiter:
    def __init__(self, limit: int, window_seconds: int = 60):
        self.limit = max(1, int(limit))
        self.window_seconds = max(1, int(window_seconds))
        self._events = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def check(self, key: str) -> None:
        now = time.monotonic()
        async with self._lock:
            events = self._events[key]
            cutoff = now - self.window_seconds
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= self.limit:
                retry_after = max(1, int(self.window_seconds - (now - events[0])))
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests",
                    headers={"Retry-After": str(retry_after)},
                )
            events.append(now)


class ConcurrencyLimiter:
    def __init__(self, limit: int):
        self.limit = max(1, int(limit))
        self._active = defaultdict(int)
        self._lock = asyncio.Lock()

    async def acquire(self, key: str) -> None:
        async with self._lock:
            if self._active[key] >= self.limit:
                raise HTTPException(status_code=429, detail="Too many concurrent streams")
            self._active[key] += 1

    async def release(self, key: str) -> None:
        async with self._lock:
            if self._active[key] <= 1:
                self._active.pop(key, None)
            else:
                self._active[key] -= 1
