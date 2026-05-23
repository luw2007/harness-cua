# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install (editable, no deps)
pip install -e .

# Run tests
pytest

# Run single test
pytest tests/test_helpers.py::test_client_call_raises_runtime_error_on_failure

# Check syntax without running
python -c "import cua_harness"

# CLI usage
echo 'print(get_screen_size())' | cua-harness
cua-harness --doctor
```

## Architecture

macOS-only Python SDK (3.11+) that wraps [cua-driver](https://github.com/trycua/cua) for AI agent desktop automation. No runtime dependencies.

### Layer stack (top → bottom)

1. **`run.py`** — CLI entrypoint. Reads stdin heredoc, calls `ensure_daemon()`, exec's code with all helpers pre-imported. Also loads `agent-workspace/agent_helpers.py` extensions if present.

2. **`helpers.py`** — 30+ tool wrapper functions (click, type_text, get_window_state, etc.). Each builds a kwargs dict and calls `_cua(tool_name, **kwargs)`. The `_cua` function delegates to `get_session().call()`. Also contains the app-skills subsystem: `_surface_app_skills()`, `save_app_skill()`, `load_app_skills()`.

3. **`session.py`** — Central `Session` object holding: a `CuaClient` instance, a `Profiler`, macro recording state, and a dry-run flag. Every tool call flows through `Session.call()` which handles dry-run gating, timing for profiler, and trajectory recording. Module-level `get_session()` / `set_default_session()` manage the singleton.

4. **`client.py`** — `CuaClient` class connecting to cua-driver daemon over Unix socket (`~/Library/Caches/cua-driver/cua-driver.sock`). Line-delimited JSON protocol: sends `{"method":"call","name":tool,"args":{...}}`, receives `{"ok":true,"result":{...}}`. Also contains `ensure_daemon()` and `kill_daemon()`.

5. **`wait.py`** — `wait_for(predicate, timeout)` polling helper.

6. **`diff.py`** — `ax_diff(before, after)` for accessibility tree diffing; `StateCapture` context manager.

7. **`dryrun.py` / `macro.py` / `profiler.py`** — Thin shims delegating to the default Session. Kept for backward-compat imports.

### App skills closed loop

The harness learns from successful operations and persists knowledge as executable Python code — not documentation or logs.

```
agent-workspace/app-skills/
  <bundle_id>/
    helpers.py              ← current callable functions
    helpers.YYYYMMDD.bak.py ← version backups (max 5, oldest-first cleanup)
    CHANGELOG.md            ← change log with reasons
```

**Lifecycle:**
1. `get_window_state(pid)` with `CUA_APP_SKILLS=1` returns `app_skills` path if `helpers.py` exists for that bundle
2. `load_app_skills(bundle_id, ns)` loads functions into a namespace for direct invocation
3. `save_app_skill(bundle_id, code, reason)` writes new `helpers.py`, backs up the previous version, appends to changelog

**Env gate:** `CUA_APP_SKILLS=1` enables surfacing. Saving always works regardless of env.

### Key design decisions

- All observability (profiler, macro, dry-run) lives in Session, not scattered across modules.
- Tool wrappers in helpers.py are pure argument builders — they never touch sockets directly.
- App-skills produce Python code (not markdown) — callable functions that bypass LLM reasoning on known paths.
- Tests mock at `cua_harness.helpers.get_session` or use `set_default_session()` to inject a Session with a mocked client. Never connect to a real daemon in tests.
- App-skills tests patch `cua_harness.helpers.AGENT_WORKSPACE` to a tmp_path fixture.
- Temporary PNG files from screenshot operations are tracked in `_tmp_files` list and cleaned via `atexit`.

## Testing patterns

All tests use `unittest.mock`. To mock the daemon connection:

```python
from cua_harness.session import Session, set_default_session
from unittest.mock import patch, MagicMock

# Create session with mocked client
with patch("cua_harness.session.CuaClient") as MockClient:
    MockClient.return_value.call.return_value = {"success": True}
    s = Session(socket_path="/tmp/fake.sock", dry_run=False)

set_default_session(s)
# ... test code ...
set_default_session(None)  # cleanup
```

Or patch at the helpers level:
```python
with patch("cua_harness.helpers.get_session", return_value=mock_session):
    result = get_screen_size(display_id=2)
```
