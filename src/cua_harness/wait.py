"""Polling helper for waiting on GUI state changes."""

import time
from typing import Callable, Any


def wait_for(
    predicate: Callable[[], Any],
    timeout: float = 10.0,
    poll_interval: float = 0.5,
    message: str | None = None,
) -> Any:
    deadline = time.monotonic() + timeout
    last_result = None
    while True:
        last_result = predicate()
        if last_result:
            return last_result
        if time.monotonic() >= deadline:
            msg = message or f"wait_for timed out after {timeout}s"
            raise TimeoutError(msg)
        remaining = deadline - time.monotonic()
        time.sleep(min(poll_interval, remaining))
