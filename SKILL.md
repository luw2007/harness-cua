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

## App skills (opt-in)

Set `CUA_APP_SKILLS=1` to enable. Off by default.

When enabled, `get_window_state` returns `app_skills` pointing to `agent-workspace/app-skills/<bundle_id>/helpers.py`. Load it into your namespace with `load_app_skills(bundle_id, ns)` then call the functions directly — no LLM reasoning needed for known paths.

After a successful operation that reveals non-obvious patterns, persist as Python code:

```python
save_app_skill("com.electron.lark", """
from cua_harness import get_window_state, click, press_key, hotkey

def open_messages(pid):
    state = get_window_state(pid, query="消息")
    click(pid, element_index=0)

def send_message(pid, text):
    from cua_harness import set_value
    state = get_window_state(pid, query="AXTextArea")
    set_value(pid, state["payload"]["structuredContent"]["windows"][0]["window_id"],
              state["payload"]["structuredContent"]["elements"][0]["index"], text)
    press_key(pid, "Return")
""", reason="learned message input path via AXTextArea")
```

Versioning:
- Each `save_app_skill` call backs up existing `helpers.py` as `helpers.YYYYMMDD.bak.py`
- Max 5 backups retained (oldest deleted first)
- Changes logged in `CHANGELOG.md`

Directory structure:
```
agent-workspace/app-skills/
  com.electron.lark/
    helpers.py           ← current (callable functions)
    helpers.20260523.bak.py
    CHANGELOG.md
  com.googlecode.iterm2/
    helpers.py
    CHANGELOG.md
```
