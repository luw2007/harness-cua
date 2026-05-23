# cua-harness

Desktop automation via cua-driver. Controls macOS apps through Accessibility APIs without stealing foreground focus.

## Tool call shape

```bash
# Heredoc mode (zero-import)
cua-harness <<'PY'
state = get_window_state(pid, capture_mode="som")
click(pid, element_index=3)
PY
```

```python
# Library mode (importable, testable, IDE-completable)
from cua_harness import ensure_daemon, get_window_state, click
ensure_daemon()
state = get_window_state(pid, capture_mode="som")
click(pid, element_index=3)
```

## Canonical loop

1. **Snapshot** — `get_window_state(pid)` returns accessibility tree + annotated screenshot
2. **Act** — `click`, `type_text`, `press_key`, `scroll`, etc. using `element_index` from snapshot
3. **Verify** — `get_window_state(pid)` again to confirm the action landed

Always snapshot before acting. Never assume UI state persists between turns.

## No-foreground contract

cua-driver operates apps WITHOUT activating them. The user's frontmost window is never disturbed. All interactions happen via Accessibility APIs on background windows.

## Available helpers

| Helper | Purpose |
|--------|---------|
| `launch_app(bundle_id, urls=None)` | Launch app, get pid |
| `list_windows(pid)` | List all windows for pid |
| `get_window_state(pid, window_id=None, capture_mode="som", query=None)` | Tree + screenshot |
| `click(pid, element_index=N)` | Click element by index |
| `click(pid, x=X, y=Y)` | Click by pixel coordinate |
| `double_click(pid, element_index=N)` | Double-click |
| `right_click(pid, element_index=N)` | Right-click / context menu |
| `drag(pid, from_x, from_y, to_x, to_y)` | Drag gesture |
| `type_text(pid, text, element_index=N)` | Type into element |
| `set_value(pid, window_id, element_index, value)` | Set form value directly |
| `press_key(pid, key, modifiers=["cmd"])` | Press key combo |
| `hotkey(pid, ["cmd", "s"])` | Shortcut |
| `scroll(pid, direction, amount=3, by="line")` | Scroll |
| `screenshot(pid)` | Capture PNG → `{"image_path": "/tmp/..."}` |
| `zoom(pid, x, y, width, height)` | Crop+upscale region → `{"image_path": "..."}` |
| `move_cursor(x, y)` | Move mouse to screen point |
| `get_cursor_position()` | Current mouse position |
| `get_screen_size()` | Display size + scale factor |
| `page(pid, action, script=None, selector=None)` | Browser JS/DOM/text |
| `list_apps()` | List all apps (running + installed) |
| `set_config(key, value)` | Write persistent driver config |
| `get_config()` | Read persistent driver config |
| `set_recording(enabled, output_dir=None)` | Toggle trajectory recording |
| `get_recording_state()` | Check recording status |
| `set_agent_cursor_enabled(enabled)` | Toggle visual cursor overlay |
| `get_agent_cursor_state()` | Read cursor config |
| `replay_trajectory(dir)` | Replay a recorded session |

## Capture modes

- `som` (default) — accessibility tree + annotated screenshot with element indices
- `ax` — accessibility tree only (no screenshot)
- `vision` — screenshot only (no tree) → returns `{"image_path": "/tmp/..."}`
- `screenshot` — raw screenshot → returns `{"image_path": "/tmp/..."}`

Image-producing calls (`screenshot()`, `zoom()`, `get_window_state(..., capture_mode="vision")`) write PNG to a temp file and return `image_path` in the result dict.

## Architecture

```
agent code
  ↓ (import or heredoc exec)
cua_harness.helpers → _cua()
  ↓
cua_harness.client → Unix socket (line-delimited JSON)
  ↓
cua-driver daemon (~/Library/Caches/cua-driver/cua-driver.sock)
  ↓
macOS AX / CoreGraphics / TCC
```

Direct socket IPC — no subprocess fork per call. Persistent connection reused across calls.

## What works best

- Use `element_index` from `som` capture for clicks — more reliable than coordinates
- Use pixel coordinates only when elements aren't in the accessibility tree
- `set_value` for text fields is faster than click + type_text
- Always re-snapshot after navigation or state changes
- Use `query` param on `get_window_state` to filter large AX trees

## Constraints

- Never call `activate` or bring windows to front
- One action per turn when unsure — snapshot to verify
- Screenshots are window-local, not full-screen
- Element indices change between snapshots — never cache them
