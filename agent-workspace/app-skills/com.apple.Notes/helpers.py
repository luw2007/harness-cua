# reason: improved Notes workflow: dismiss welcome sheet before create/search

from cua_harness import get_window_state, click, press_key, hotkey, type_text, list_windows


def _structured(result):
    return result.get('payload', {}).get('structuredContent', result)


def _main_window_id(pid):
    windows = _structured(list_windows(pid)).get('windows', [])
    visible = [w for w in windows if w.get('is_on_screen') and w.get('on_current_space')]
    if not visible:
        visible = [w for w in windows if w.get('on_current_space')]
    if not visible:
        return None
    titled = [w for w in visible if w.get('title')]
    return (titled or visible)[0].get('window_id')


def ensure_notes_ready(pid):
    window_id = _main_window_id(pid)
    state = get_window_state(pid, window_id=window_id, capture_mode='som') if window_id else get_window_state(pid, capture_mode='som')
    if '继续' in str(state):
        click(pid, window_id=window_id, element_index=5)
    return window_id


def create_note(pid, title, body):
    ensure_notes_ready(pid)
    hotkey(pid, ['command', 'n'])
    type_text(pid, title)
    press_key(pid, 'Return')
    type_text(pid, body)


def search_note(pid, query):
    ensure_notes_ready(pid)
    hotkey(pid, ['command', 'f'])
    type_text(pid, query)
