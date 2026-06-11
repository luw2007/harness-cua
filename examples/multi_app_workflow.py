#!/usr/bin/env python3
"""Multi-app workflow: copy a file path from Finder and paste into Notes.

Demonstrates:
- Managing multiple app PIDs simultaneously
- Cross-app automation (Finder → Notes)
- Auto window selection (no explicit window_id needed)
- Keyboard shortcuts for system-level operations
"""

from cua_harness import (
    click,
    get_window_state,
    hotkey,
    launch_app,
    screenshot,
)


def main():
    # --- Launch both apps ---
    finder = launch_app(bundle_id="com.apple.finder")
    pid_finder = finder["pid"]
    print(f"Finder launched: pid={pid_finder}, windows={len(finder['windows'])}")

    notes = launch_app(bundle_id="com.apple.Notes")
    pid_notes = notes["pid"]
    print(f"Notes launched: pid={pid_notes}, windows={len(notes['windows'])}")

    # --- Work in Finder: select a file and copy its path ---
    finder_state = get_window_state(pid_finder, capture_mode="som")
    print(f"Finder elements: {finder_state.get('element_count', 0)}")

    # Click the first file in the file list (element_index depends on actual UI)
    # In practice, inspect finder_state['tree_markdown'] to find the right index
    file_index = 5  # typically the first item in a Finder list view
    click(pid_finder, element_index=file_index)
    print(f"Selected file at element_index={file_index}")

    # Copy file path: Cmd+Option+C
    hotkey(pid_finder, keys=["command", "option", "c"])
    print("Copied file path to clipboard")

    # --- Switch to Notes: paste the path ---
    notes_state = get_window_state(pid_notes, capture_mode="som")
    print(f"Notes elements: {notes_state.get('element_count', 0)}")

    # Click the note body area to focus it
    # Look for a text editing area in the element tree
    body_index = 3  # typically the note content area
    click(pid_notes, element_index=body_index)
    print(f"Clicked Notes body at element_index={body_index}")

    # Paste: Cmd+V
    hotkey(pid_notes, keys=["command", "v"])
    print("Pasted file path into Notes")

    # --- Capture final state of both windows ---
    finder_shot = screenshot(pid_finder)
    print(f"Finder screenshot: {finder_shot.get('path', 'captured')}")

    notes_shot = screenshot(pid_notes)
    print(f"Notes screenshot: {notes_shot.get('path', 'captured')}")

    print("\nWorkflow complete: file path copied from Finder → pasted into Notes")


if __name__ == "__main__":
    main()
