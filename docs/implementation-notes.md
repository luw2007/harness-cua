# Implementation Notes

## Decisions not in spec

1. **Tool name format**: cua-driver uses `snake_case` tool names (e.g., `check_permissions`, `launch_app`, `get_window_state`), not `kebab-case` as initially assumed. Discovered via `--doctor` error output listing available tools.

2. **`double_click` as independent tool**: cua-driver has a dedicated `double_click` tool rather than `click` with `count=2`. Updated to call the native tool directly.

3. **`app_info()` maps to `list_apps`**: cua-driver doesn't have an `app-info` tool. Kept `list_apps` as primary name, `app_info` as backward-compat alias.

4. **`_doctor` delegates to `cua-driver doctor`**: Rather than reimplementing permission checks, we shell out to the native doctor command and handle TimeoutExpired gracefully (daemon likely not running).

5. **`cua-driver call` subcommand required**: Tool invocation is `cua-driver call <tool> [json-args]`, NOT `cua-driver <tool> <json-args>`. The `call` subcommand is mandatory. (NOTE: now bypassed — socket IPC talks directly to daemon)

6. **`cua-driver status` takes no positional args**: Unlike `call`, `status` only accepts optional `--socket` and `--pid-file` flags. (NOTE: now bypassed — we check socket connectivity directly)

7. **`cua-driver serve` handles TCC relaunch internally**: The serve subcommand auto-detects non-TCC-attributed contexts and re-execs via `open -n -g -a CuaDriver --args serve`. No need for the harness to do this — bare `Popen(["cua-driver", "serve"])` is correct.

8. **`screenshot_out_file` as daemon arg**: When using socket IPC, the `screenshot_out_file` key is passed as part of the JSON args (not a CLI flag). Daemon writes PNG to the specified path.

9. **Socket protocol is line-delimited JSON**: Discovered via `cua-driver serve --help`. Protocol: `{"method":"call","name":"<tool>","args":{...}}` → `{"ok":true,"result":{...}}`. No framing beyond newline.

10. **32 tools total (not 22)**: cua-driver exposes more tools than originally scoped. Added: `get_config`, `set_config`, `set_recording`, `get_recording_state`, `get_agent_cursor_state`, `set_agent_cursor_enabled`, `set_agent_cursor_motion`, `set_agent_cursor_style`, `replay_trajectory`. Exposed the most useful subset (32 functions including aliases).

## v0.2.0 Refactor — subprocess → socket IPC

**Problem**: Original design forked a `cua-driver call` subprocess for every tool invocation. This added ~5-15ms overhead per call (process spawn + CLI arg parsing + socket connect inside the CLI). In agent loops with 10-50 calls per turn, this accumulated to 50-750ms of pure waste.

**Solution**: Direct Unix socket client (`cua_harness.client.CuaClient`) that maintains a persistent connection to the daemon. Protocol is trivial line-delimited JSON — no need for the CLI intermediary.

**Changes**:
- New `client.py`: `CuaClient` class with connect/send/receive/reconnect
- `helpers.py` rewritten: `_cua()` now calls `get_client().call()` instead of `subprocess.run()`
- `__init__.py`: full `__all__` export for `from cua_harness import *`
- `run.py`: `_build_namespace()` from `__all__`, `try/except` around exec, `_load_agent_helpers` wrapped

**P0 fixes included**:
- JSONDecodeError → `RuntimeError` (daemon protocol guarantees JSON, so non-JSON = bug)
- tmp PNG cleanup via `atexit.register(_cleanup_tmp_files)`
- `ensure_daemon` captures stderr, includes in RuntimeError message

**P1 fixes included**:
- `exec` wrapped in `try/except` + `traceback.print_exc()`
- `_load_agent_helpers` wrapped in `try/except` with warning

## Things changed from plan

- Plan said `check-permissions` (kebab) — actual tool is `check_permissions` (snake)
- Plan said `app_info()` maps to `app-info` — mapped to `list_apps` instead (kept `app_info` as alias)
- Plan said direct tool invocation (`cua-driver <tool>`) — actual requires `cua-driver call <tool>`
- Plan didn't address screenshot binary handling — added `screenshot_out_file` param pattern
- Original plan used subprocess IPC — replaced with direct socket for v0.2.0

## Tradeoffs

- **Socket vs subprocess**: Socket is faster (~0.5ms vs ~10ms per call) but requires daemon to be running. `ensure_daemon()` handles cold start. If socket dies mid-session, next `_cua()` call raises `ConnectionError` — caller must retry or restart daemon.
- **No async client yet**: Synchronous socket is fine for single-threaded agent loops. Async version (`AsyncCuaClient`) deferred to v0.3.0.
- **`ensure_daemon` still uses subprocess for `cua-driver serve`**: Can't avoid this — need to start the process. But it's a one-time cost per session.
- **Temp PNG cleanup is atexit only**: If process crashes hard (SIGKILL), temp files leak. Acceptable tradeoff — OS cleans `/tmp` periodically.
- **`screenshot_out_file` passed in args dict**: Socket protocol sends it as a regular tool argument. Daemon handles file writing. If daemon can't write (permissions), it returns `ok:false`.

## v0.3.2 — Robustness fixes from browser-harness comparison (2026-05-24)

**Context**: Compared browser-harness (365+ commits, 60+ bug fixes) with harness-cua and identified missing robustness patterns.

**Rejected (architectural mismatch)**:
- PID reuse identity verification: browser-harness needs this because it uses TCP ports which can collide. harness-cua uses AF_UNIX sockets (path-bound, no collision possible).
- alive() semantic ping/pong: AF_UNIX socket path already proves identity. `{"method":"list"}` response validation is sufficient.

**Applied (3 fixes, all in client.py)**:

1. **`_send()` stale connection auto-reconnect**: If daemon restarts while client holds a cached socket, the first send gets BrokenPipe. Now retries once with a fresh connection instead of propagating the error immediately.

2. **`ensure_daemon()` retry on transient failure**: If first spawn fails with "address already in use" (stale socket from previous slow shutdown), unlinks the socket and retries once. Other errors still fail immediately.

3. **`kill_daemon()` socket cleanup**: Unlinks socket file after kill to prevent stale-socket issues on next daemon_alive() check.

**Decision**: browser-harness's complexity (identify/verify PID, process start-time fingerprinting, backward-compat ping fallback) is over-engineering for our case. cua-driver is a separate managed binary, not our own daemon — simpler client-side resilience is correct.
