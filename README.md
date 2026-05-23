# cua-harness

Agent-friendly Python SDK for desktop automation via [cua-driver](https://github.com/trycua/cua).

![macOS only](https://img.shields.io/badge/platform-macOS-lightgrey)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

## Install

Prerequisites: [cua-driver](https://github.com/trycua/cua) installed and on PATH.

```bash
pip install cua-harness
```

From source:

```bash
git clone https://github.com/anthropics/cua-harness.git
cd cua-harness
pip install -e .
```

## Quick Start

### Heredoc CLI

```bash
cua-harness <<'PY'
result = launch_app("com.apple.Safari")
pid = result["pid"]
state = get_window_state(pid, capture_mode="som")
click(pid, element_index=5)
type_text(pid, "hello world")
PY
```

### Library

```python
from cua_harness import ensure_daemon, launch_app, get_window_state, click, type_text

ensure_daemon()
app = launch_app("com.apple.Safari")
pid = app["pid"]
state = get_window_state(pid)
click(pid, element_index=3)
type_text(pid, "search query")
```

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Agent Code (heredoc / library / framework)     │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│  cua_harness.helpers                            │
│  30+ tool wrappers: click, type_text, scroll…   │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│  cua_harness.session                            │
│  Profiler · Macro Recorder · Dry-run Gate       │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│  cua_harness.client (Unix socket IPC)           │
│  Line-delimited JSON protocol                   │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│  cua-driver daemon                              │
│  macOS Accessibility + Screen Capture APIs       │
└─────────────────────────────────────────────────┘
```

## API Reference

### App & Window

| Function | Description |
|----------|-------------|
| `ensure_daemon()` | Start cua-driver daemon if not running |
| `launch_app(bundle_id=, name=)` | Launch app by bundle ID or name |
| `list_apps()` | List running applications |
| `list_windows(pid)` | List windows for a process |
| `get_window_state(pid, capture_mode="som")` | Get AX tree / screenshot |

### Input

| Function | Description |
|----------|-------------|
| `click(pid, element_index=, x=, y=, count=)` | Click element or coordinates |
| `double_click(pid, element_index=)` | Double-click |
| `right_click(pid, element_index=)` | Right-click |
| `type_text(pid, text, delay_ms=)` | Type text into focused element |
| `press_key(pid, key, modifiers=)` | Press keyboard key |
| `hotkey(pid, keys)` | Press key combination |
| `set_value(pid, window_id, element_index, value)` | Set element value directly |

### Navigation

| Function | Description |
|----------|-------------|
| `scroll(pid, direction, amount=3)` | Scroll in direction |
| `drag(pid, from_x, from_y, to_x, to_y)` | Drag gesture |
| `move_cursor(x, y)` | Move mouse cursor |
| `get_cursor_position()` | Get current cursor position |
| `get_screen_size(display_id=)` | Screen dimensions (multi-monitor) |
| `zoom(pid, x, y, width, height)` | Capture zoomed region |

### Observability

| Function | Description |
|----------|-------------|
| `wait_for(predicate, timeout=10)` | Poll until condition met |
| `ax_diff(before, after)` | Diff two AX tree snapshots |
| `StateCapture(pid)` | Context manager for before/after diff |
| `set_dry_run(enabled)` | Toggle dry-run mode |
| `profile()` | Context manager for latency profiling |
| `start_recording()` / `stop_recording(path=)` | Macro record |
| `replay(path, speed=1.0)` | Replay recorded trajectory |

### App Skills (Learning Loop)

| Function | Description |
|----------|-------------|
| `save_app_skill(bundle_id, code, reason="")` | Persist learned Python helpers for an app |
| `load_app_skills(bundle_id, ns)` | Load app's helpers.py into namespace |

`get_window_state()` automatically returns `app_skills` path when a bundle has learned helpers. In heredoc CLI mode, all app-skills are auto-loaded into the namespace.

## Examples

### Wait for UI state

```python
from cua_harness import wait_for, get_window_state

def dialog_appeared():
    state = get_window_state(pid)
    return any(e.get("role") == "dialog" for e in state.get("elements", []))

wait_for(dialog_appeared, timeout=5, message="dialog did not appear")
```

### AX tree diff

```python
from cua_harness import get_window_state, ax_diff, click

before = get_window_state(pid)
click(pid, element_index=7)
after = get_window_state(pid)

diff = ax_diff(before, after)
print(diff["summary"])  # "+2 -0 ~1"
```

### Macro record and replay

```python
from cua_harness import start_recording, stop_recording, replay, click, type_text

start_recording()
click(pid, element_index=3)
type_text(pid, "automated input")
stop_recording("my_macro.json")

# Later:
replay("my_macro.json", speed=2.0)
```

### Performance profiling

```python
from cua_harness import profile, click, get_window_state

with profile() as p:
    for i in range(10):
        get_window_state(pid)
        click(pid, element_index=i)
# Prints: tool name, call count, avg/min/max latency
```

### Dry-run mode

```python
from cua_harness import set_dry_run, click, get_window_state

set_dry_run(True)
click(pid, element_index=5)       # logged to stderr, not executed
get_window_state(pid)             # executes normally (read-only)
set_dry_run(False)
```

### App skills — learn and reuse

```python
from cua_harness import save_app_skill, load_app_skills

# After successfully automating Lark, persist the helpers:
save_app_skill("com.electron.lark", """
from cua_harness import get_window_state, click, set_value, press_key

def open_messages(pid):
    state = get_window_state(pid, query="消息")
    click(pid, element_index=0)

def send_message(pid, window_id, element_index, text):
    set_value(pid, window_id, element_index, text)
    press_key(pid, "Return")
""", reason="learned message tab path via AXRadioButton")

# In heredoc CLI mode, app-skills are auto-loaded — call directly:
#   open_messages(pid)
#   send_message(pid, wid, idx, "hello")
#
# In library mode, load manually:
ns = {}
load_app_skills("com.electron.lark", ns)
ns["open_messages"](pid)
ns["send_message"](pid, wid, idx, "hello")
```

Versioning: each save backs up the previous `helpers.py` as `helpers.YYYYMMDD.bak.py` (max 5 kept). Changes logged in `CHANGELOG.md` per bundle.

## Comparison

| Feature | cua-harness | pyautogui | osascript | Playwright |
|---------|:-----------:|:---------:|:---------:|:----------:|
| Accessibility tree | yes | no | partial | no (web only) |
| Element-based targeting | yes | no | partial | yes (web) |
| No foreground steal | yes | no | yes | n/a |
| Multi-display | yes | partial | no | n/a |
| Dry-run mode | yes | no | no | no |
| Performance profiler | yes | no | no | yes |
| Macro record/replay | yes | no | no | yes |
| Agent-friendly API | yes | no | no | partial |
| Platform | macOS | cross | macOS | cross (web) |

## Permissions

macOS requires Accessibility and Screen Recording permissions via TCC. Grant access to your terminal in System Settings > Privacy & Security.

See [docs/tcc-permissions.md](docs/tcc-permissions.md) for detailed setup.

## Contributing

Issues and pull requests welcome.

```bash
pip install -e .
pytest
```

## License

MIT
