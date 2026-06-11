"""
Minimal Claude Code agent skill that drives a macOS app via cua-harness.

This demonstrates an external agent framework (Claude Code) integrating with
cua-harness as its GUI automation backend. The agent:
1. Launches an app
2. Waits for it to be ready (wait_for)
3. Captures state with profiling enabled
4. Performs actions with dry-run safety
5. Diffs the AX tree to verify the action took effect

Usage from Claude Code heredoc:
    cua-harness <<'PY'
    exec(open("examples/claude_code_agent.py").read())
    PY

Or as a library:
    from examples.claude_code_agent import run_agent
    run_agent("com.apple.TextEdit")
"""

from cua_harness import (
    ax_diff,
    ensure_daemon,
    get_window_state,
    is_dry_run,
    launch_app,
    list_windows,
    profile,
    set_dry_run,
    type_text,
    wait_for,
)


def run_agent(bundle_id: str = "com.apple.TextEdit", dry_run: bool = True):
    """Drive an app end-to-end with observability."""

    ensure_daemon()
    set_dry_run(dry_run)

    with profile():
        # 1. Launch the target app
        app = launch_app(bundle_id=bundle_id)
        pid = app.get("pid") or app.get("process_id")
        if not pid:
            print(f"Failed to get PID from launch_app: {app}")
            return

        # 2. Wait for at least one window to appear
        def has_windows():
            result = list_windows(pid)
            windows = result.get("windows", [])
            return windows if windows else None

        windows = wait_for(has_windows, timeout=10, message=f"{bundle_id} did not open a window")
        window_id = windows[0].get("window_id")
        print(f"App launched: pid={pid}, window_id={window_id}")

        # 3. Capture initial state
        before = get_window_state(pid, window_id=window_id)
        print(f"Initial state: {len(before.get('elements', []))} elements")

        # 4. Perform an action (type text into the app)
        type_text(pid, text="Hello from cua-harness agent!", window_id=window_id)

        # 5. Capture post-action state and diff
        after = get_window_state(pid, window_id=window_id)
        diff = ax_diff(before, after)
        print(f"AX diff: {diff['summary']}")

        if diff["changed"]:
            for c in diff["changed"][:3]:
                print(f"  index {c['index']}: {c['changes']}")

    # Profiler auto-prints report on exit from `with profile()`
    print(f"\nDry-run mode: {is_dry_run()}")
    print("Agent run complete.")


if __name__ == "__main__":
    import sys
    bundle = sys.argv[1] if len(sys.argv) > 1 else "com.apple.TextEdit"
    dry = "--live" not in sys.argv
    run_agent(bundle_id=bundle, dry_run=dry)
