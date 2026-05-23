# cua-harness

Agent-friendly Python SDK for desktop automation via [cua-driver](https://github.com/trycua/cua).

![macOS only](https://img.shields.io/badge/platform-macOS-lightgrey)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

## Install

Prerequisites: [cua-driver](https://github.com/trycua/cua) installed (`brew install trycua/tap/cua` or see upstream docs).

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
pid = result["data"]["pid"]
state = get_window_state(pid, capture_mode="som")
click(pid, element_index=5)
type_text(pid, "hello world")
PY
```

### Library

```python
from cua_harness import click, type_text, get_window_state, ensure_daemon

ensure_daemon()
state = get_window_state(pid, capture_mode="ax")
click(pid, element_index=3)
type_text(pid, "search query")
```

## Features

- **30+ tool wrappers** -- click, type_text, press_key, scroll, screenshot, get_window_state, drag, launch_app, and more
- **wait_for(predicate, timeout)** -- polling helper that blocks until a condition is met or times out
- **ax_diff()** -- diff accessibility tree snapshots to detect UI state changes
- **Multi-display** -- `get_screen_size(display_id=)` for multi-monitor setups
- **Macro record/replay** -- capture and replay interaction sequences
- **Performance profiler** -- per-tool latency statistics
- **Dry-run mode** -- mutations logged but not executed (for testing agent plans)
- **Socket IPC** -- communicates with cua-driver daemon over Unix socket, no subprocess shelling

## Permissions

macOS requires Accessibility and Screen Recording entitlements via TCC (Transparency, Consent, and Control). Grant access to your terminal emulator in System Settings > Privacy & Security.

See [docs/tcc-permissions.md](docs/tcc-permissions.md) for detailed setup.

## Contributing

Issues and pull requests welcome. Run the test suite before submitting:

```bash
pytest
```

## License

MIT
