# reason: learned New Note button path via element_index=0

from cua_harness import get_window_state, click, type_text, press_key

def create_note(pid, content):
    state = get_window_state(pid, capture_mode='som')
    click(pid, element_index=0)
    type_text(pid, content)
    press_key(pid, "Return")
