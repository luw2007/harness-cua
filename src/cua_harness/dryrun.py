"""Dry-run compat shims — delegates to default Session."""

import sys

from cua_harness.session import get_session, MUTATION_TOOLS


def set_dry_run(enabled: bool) -> None:
    get_session().dry_run = enabled


def is_dry_run() -> bool:
    return get_session().dry_run


def should_skip(tool: str) -> bool:
    if not get_session().dry_run:
        return False
    return tool in MUTATION_TOOLS


def log_skipped(tool: str, kwargs: dict) -> dict:
    print(f"[dry-run] SKIP {tool}({kwargs})", file=sys.stderr)
    return {"success": True, "dry_run": True, "tool": tool, "args": kwargs}
