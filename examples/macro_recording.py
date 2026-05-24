#!/usr/bin/env python3
"""Macro recording lifecycle: record Calculator interactions, save, and replay."""

import json
import time

from cua_harness import (
    ensure_daemon,
    launch_app,
    start_macro,
    stop_macro,
    replay_macro,
    click,
    get_window_state,
)

MACRO_PATH = "/tmp/calc_macro.json"

def main():
    ensure_daemon()

    # Launch Calculator
    app = launch_app(bundle_id="com.apple.Calculator")
    pid = app["pid"]
    print(f"Calculator launched, pid={pid}")
    time.sleep(1)

    # Get window state to find element indices
    state = get_window_state(pid)
    window_id = state.get("window_id")
    print(f"Window ready, window_id={window_id}")

    # Start recording
    start_macro()
    print("Recording started...")

    # Perform some calculator operations (click by element_index)
    click(pid, window_id=window_id, element_index=5)   # digit
    time.sleep(0.3)
    click(pid, window_id=window_id, element_index=10)  # operator
    time.sleep(0.3)
    click(pid, window_id=window_id, element_index=3)   # digit
    time.sleep(0.3)
    click(pid, window_id=window_id, element_index=15)  # equals

    # Stop recording and save
    trajectory = stop_macro(MACRO_PATH)
    print(f"\nRecording stopped. {len(trajectory)} steps saved to {MACRO_PATH}")

    # Show trajectory structure
    if trajectory:
        print(f"Trajectory record keys: {list(trajectory[0].keys())}")
        print(f"Total duration: {trajectory[-1]['t']:.2f}s")

    # Preview saved JSON
    saved = json.loads(open(MACRO_PATH).read())
    print(f"Saved JSON: {len(saved)} entries, {len(json.dumps(saved))} bytes")
    # Replay at 2x speed
    print("\nReplaying at 2x speed...")
    results = replay_macro(MACRO_PATH, speed=2.0)
    print(f"Replay complete: {len(results)} steps executed")


if __name__ == "__main__":
    main()
