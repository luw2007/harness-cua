# reason: learned iTerm2 tab/pane management and command execution

from cua_harness import hotkey, type_text, press_key


def new_tab(pid):
    hotkey(pid, "Command+t")


def split_pane_vertical(pid):
    hotkey(pid, "Command+d")


def split_pane_horizontal(pid):
    hotkey(pid, "Command+Shift+d")


def run_command(pid, cmd):
    type_text(pid, cmd)
    press_key(pid, "Return")


def clear_terminal(pid):
    hotkey(pid, "Command+k")
