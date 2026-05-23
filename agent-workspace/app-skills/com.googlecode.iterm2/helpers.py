from cua_harness import hotkey, type_text, press_key


def new_tab(pid):
    """Open a new tab via Cmd+T."""
    hotkey(pid, "Command+t")


def split_pane_vertical(pid):
    """Split pane vertically via Cmd+D."""
    hotkey(pid, "Command+d")


def split_pane_horizontal(pid):
    """Split pane horizontally via Cmd+Shift+D."""
    hotkey(pid, "Command+Shift+d")


def run_command(pid, cmd):
    """Type a command and press Enter."""
    type_text(pid, cmd)
    press_key(pid, "Return")


def clear_terminal(pid):
    """Clear terminal via Cmd+K."""
    hotkey(pid, "Command+k")
