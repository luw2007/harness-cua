# Basic GUI automation example.
# Requires cua-driver daemon running: cua-driver start
#
# Usage:
#     cua-harness <<'PY'
#     exec(open("examples/basic_automation.py").read())
#     PY

import time
from cua_harness import (
    get_screen_size,
    launch_app,
    get_window_state,
    click,
    type_text,
    hotkey,
    screenshot,
)


def main():
    # 1. Screen size
    print("1. Getting screen size...")
    size = get_screen_size()
    print(f"   Screen: {size}")

    # 2. Launch TextEdit
    print("2. Launching TextEdit...")
    result = launch_app(bundle_id="com.apple.TextEdit")
    pid = result["pid"]
    print(f"   PID: {pid}")
    time.sleep(1.0)

    # 3. Window state (auto-selects window_id)
    print("3. Getting window state...")
    state = get_window_state(pid, capture_mode="som")
    window_id = state.get("window_id")
    print(f"   Elements: {state.get('element_count', '?')}, window_id={window_id}")

    # 4. Type some text
    print("4. Typing text...")
    hotkey(pid, ["command", "n"])  # new document
    time.sleep(0.5)
    click(pid, x=400, y=300)
    time.sleep(0.3)
    type_text(pid, "Hello from cua-harness!\nThis is an automated GUI test.")
    time.sleep(0.5)

    # 5. Save via Cmd+S
    print("5. Saving file...")
    hotkey(pid, ["command", "s"])
    time.sleep(1.0)

    # 6. Screenshot
    print("6. Taking screenshot...")
    img = screenshot(pid, window_id=window_id)
    print(f"   Screenshot: {img.get('image_path', img)}")

    print("Done.")


if __name__ == "__main__":
    main()
