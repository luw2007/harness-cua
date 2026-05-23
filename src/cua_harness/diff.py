"""AX tree diff: compare two get_window_state snapshots."""

from typing import Any


def _index_elements(state: dict) -> dict[int, dict]:
    elements = state.get("elements") or state.get("result", {}).get("elements") or []
    return {e.get("index", i): e for i, e in enumerate(elements)}


def _element_identity(el: dict) -> str:
    return f"{el.get('role', '')}:{el.get('title', '')}"


def ax_diff(before: dict, after: dict) -> dict:
    before_els = _index_elements(before)
    after_els = _index_elements(after)

    added = []
    removed = []
    changed = []

    common_indices = set(before_els.keys()) & set(after_els.keys())
    before_only = set(before_els.keys()) - set(after_els.keys())
    after_only = set(after_els.keys()) - set(before_els.keys())

    for i in common_indices:
        b, a = before_els[i], after_els[i]
        if b != a:
            changes = {}
            for k in set(list(b.keys()) + list(a.keys())):
                if b.get(k) != a.get(k):
                    changes[k] = {"before": b.get(k), "after": a.get(k)}
            if changes:
                changed.append({"index": i, "changes": changes})

    before_identities = {_element_identity(e) for e in before_els.values()}
    after_identities = {_element_identity(e) for e in after_els.values()}

    for i in after_only:
        e = after_els[i]
        if _element_identity(e) not in before_identities:
            added.append(e)

    for i in before_only:
        e = before_els[i]
        if _element_identity(e) not in after_identities:
            removed.append(e)

    return {
        "added": added,
        "removed": removed,
        "changed": changed,
        "summary": f"+{len(added)} -{len(removed)} ~{len(changed)}",
    }


class StateCapture:
    """Context manager that captures before/after window state and diffs."""

    def __init__(self, pid: int, window_id: int | None = None, capture_mode: str = "som"):
        self._pid = pid
        self._window_id = window_id
        self._capture_mode = capture_mode
        self.before: dict | None = None
        self.after: dict | None = None
        self.diff: dict | None = None

    def __enter__(self):
        from cua_harness.helpers import get_window_state
        self.before = get_window_state(self._pid, window_id=self._window_id, capture_mode=self._capture_mode)
        return self

    def __exit__(self, *_):
        from cua_harness.helpers import get_window_state
        self.after = get_window_state(self._pid, window_id=self._window_id, capture_mode=self._capture_mode)
        self.diff = ax_diff(self.before, self.after)
