# cua-harness

macOS-only Python SDK wrapping [cua-driver](https://github.com/trycua/cua) for AI agent desktop automation.

![macOS only](https://img.shields.io/badge/platform-macOS-lightgrey)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

**Features:** structuredContent auto-unwrap, smart window selection, app-skills closed-loop learning.

## Install

Prerequisites: [cua-driver](https://github.com/trycua/cua) installed and on PATH.

Install cua-driver (macOS):
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/trycua/cua/main/libs/cua-driver/scripts/install.sh)"
# verify
which cua-driver
cua-harness --doctor
```

```bash
pip install -e .
```

## Quick Start

```python
from cua_harness import ensure_daemon, launch_app, get_window_state, click, type_text

ensure_daemon()

# launch_app returns unwrapped result — pid/windows directly accessible
result = launch_app(bundle_id='com.apple.finder')
pid = result['pid']           # int, ready to use
windows = result['windows']   # list of window dicts

# get_window_state auto-selects visible window when window_id omitted
state = get_window_state(pid, capture_mode='som')
# state['app_skills'] surfaces learned helpers path if available

click(pid, element_index=3)
type_text(pid, "hello world")
```

## Macro Recording

```python
from cua_harness import start_macro, stop_macro, replay_macro

start_macro()
# ... perform operations ...
trajectory = stop_macro('/tmp/my_macro.json')

# replay at 2x speed
replay_macro('/tmp/my_macro.json', speed=2.0)
```

## App Skills (Closed-Loop Learning)

The harness learns from successful operations and persists knowledge as executable Python code.

```
agent-workspace/app-skills/
  <bundle_id>/
    helpers.py          # current callable functions
    helpers.prev.py     # single previous version backup
```

**Lifecycle:**

1. Agent explores an app via `get_window_state` + `click` / `type_text`
2. Successful sequence saved: `save_app_skill(bundle_id, code, reason)`
3. Next `get_window_state(pid)` auto-returns `app_skills` path in response
4. Agent calls learned functions directly — skips LLM reasoning on known paths

```python
from cua_harness import save_app_skill, get_window_state

# After discovering a reliable path, persist it:
save_app_skill("com.apple.finder", """
from cua_harness import get_window_state, click, press_key

def open_folder(pid, folder_name):
    state = get_window_state(pid, query=folder_name)
    click(pid, element_index=0)
""", reason="reliable sidebar navigation via AXOutline")

# Next session — get_window_state returns app_skills path automatically
state = get_window_state(pid)
# state['app_skills'] = 'agent-workspace/app-skills/com.apple.finder/helpers.py'
# In heredoc CLI mode, functions are auto-loaded into namespace
```

## CLI Usage

```bash
# Execute Python with all helpers pre-imported
echo 'print(get_screen_size())' | cua-harness

# Heredoc mode
cua-harness <<'PY'
result = launch_app("com.apple.Safari")
pid = result["pid"]
state = get_window_state(pid, capture_mode="som")
click(pid, element_index=5)
PY

# Health check
cua-harness --doctor
```

## Architecture

```
run.py          CLI entrypoint, heredoc exec, auto-loads app-skills
    │
helpers.py      30+ tool wrappers (click, type_text, get_window_state...)
    │
session.py      Session singleton: profiler, macro, dry-run gate
    │
client.py       CuaClient — Unix socket, line-delimited JSON protocol
    │
cua-driver      macOS Accessibility + Screen Capture daemon
```

## Testing

```bash
pytest

# Single test
pytest tests/test_helpers.py::test_client_call_raises_runtime_error_on_failure
```

Tests mock at `cua_harness.helpers.get_session` — never connect to a real daemon.

## Security model

cua-harness executes arbitrary Python by design:

- The CLI reads code from stdin (heredoc) and `exec`s it with all helpers pre-imported.
- It auto-loads `agent-workspace/agent_helpers.py` from the current working directory if present.
- It auto-loads every `agent-workspace/app-skills/<bundle_id>/helpers.py` from the current working directory into the exec namespace.

All three are arbitrary code execution paths. Do not run `cua-harness` inside an untrusted directory — a malicious `agent_helpers.py` or app-skill `helpers.py` will execute with your privileges. Treat any cloned repo's `agent-workspace/` as untrusted code until reviewed.

## License

MIT
