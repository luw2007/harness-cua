# reason: improved Finder helper by opening a fresh Finder window before Go to Folder

import time
from cua_harness import hotkey, press_key, type_text


def navigate_to(pid, path):
    # Finder shortcuts are most reliable after creating a fresh foreground window.
    hotkey(pid, ['command', 'n'])
    time.sleep(0.7)
    hotkey(pid, ['command', 'shift', 'g'])
    time.sleep(0.7)
    type_text(pid, path)
    time.sleep(0.2)
    press_key(pid, 'Return')
    time.sleep(1.2)


def new_folder(pid, name):
    hotkey(pid, ['command', 'shift', 'n'])
    time.sleep(0.7)
    type_text(pid, name)
    time.sleep(0.2)
    press_key(pid, 'Return')
    time.sleep(1.2)
