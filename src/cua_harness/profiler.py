"""Performance profiler for cua-harness tool calls."""

import time
from contextlib import contextmanager
from dataclasses import dataclass, field


@dataclass
class ToolStats:
    call_count: int = 0
    total_ms: float = 0.0
    min_ms: float = float("inf")
    max_ms: float = 0.0

    @property
    def avg_ms(self) -> float:
        return self.total_ms / self.call_count if self.call_count else 0.0

    def record(self, elapsed_ms: float) -> None:
        self.call_count += 1
        self.total_ms += elapsed_ms
        self.min_ms = min(self.min_ms, elapsed_ms)
        self.max_ms = max(self.max_ms, elapsed_ms)


@dataclass
class Profiler:
    tools: dict[str, ToolStats] = field(default_factory=dict)
    _active: bool = False
    _session_start: float = 0.0

    def start(self) -> "Profiler":
        self._active = True
        self._session_start = time.monotonic()
        self.tools = {}
        return self

    def stop(self) -> "Profiler":
        self._active = False
        return self

    @property
    def active(self) -> bool:
        return self._active

    def record(self, tool: str, elapsed_ms: float) -> None:
        if not self._active:
            return
        if tool not in self.tools:
            self.tools[tool] = ToolStats()
        self.tools[tool].record(elapsed_ms)

    @property
    def elapsed_s(self) -> float:
        if self._session_start == 0:
            return 0.0
        return time.monotonic() - self._session_start

    def report(self) -> dict:
        rows = {}
        for name, stats in sorted(self.tools.items(), key=lambda x: -x[1].total_ms):
            rows[name] = {
                "calls": stats.call_count,
                "total_ms": round(stats.total_ms, 1),
                "avg_ms": round(stats.avg_ms, 1),
                "min_ms": round(stats.min_ms, 1),
                "max_ms": round(stats.max_ms, 1),
            }
        return {
            "elapsed_s": round(self.elapsed_s, 2),
            "total_calls": sum(s.call_count for s in self.tools.values()),
            "tools": rows,
        }

    def print_report(self) -> None:
        r = self.report()
        print(f"\n{'='*60}")
        print(f"cua-harness profiler | {r['elapsed_s']}s | {r['total_calls']} calls")
        print(f"{'='*60}")
        print(f"{'tool':<25} {'calls':>5} {'total':>8} {'avg':>7} {'min':>7} {'max':>7}")
        print(f"{'-'*60}")
        for name, s in r["tools"].items():
            print(f"{name:<25} {s['calls']:>5} {s['total_ms']:>7.1f}ms {s['avg_ms']:>6.1f}ms {s['min_ms']:>6.1f}ms {s['max_ms']:>6.1f}ms")
        print()


_global_profiler = Profiler()


def get_profiler() -> Profiler:
    from cua_harness.session import get_session
    return get_session().profiler


@contextmanager
def profile():
    from cua_harness.session import get_session
    p = get_session().profiler
    p.start()
    try:
        yield p
    finally:
        p.stop()
        p.print_report()
