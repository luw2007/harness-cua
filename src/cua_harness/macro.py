"""Macro compat shims — delegates to default Session."""

from cua_harness.session import get_session


def start_recording() -> None:
    get_session().start_recording()


def stop_recording(output_path: str | None = None) -> list[dict]:
    return get_session().stop_recording(output_path)


def is_recording() -> bool:
    return get_session().is_recording


def record_call(tool: str, kwargs: dict, result=None) -> None:
    pass


def replay(path: str, speed: float = 1.0) -> list[dict]:
    return get_session().replay(path, speed)
