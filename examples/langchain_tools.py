"""
LangChain-style tool integration for cua-harness.

Shows how any agent framework that uses a Tool abstraction (LangChain, CrewAI,
AutoGen, etc.) can wrap cua-harness functions as callable tools.

This is a standalone adapter — no LangChain dependency required.
Agent frameworks can import these Tool objects directly.
"""

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Tool:
    """Minimal tool interface compatible with LangChain/CrewAI patterns."""
    name: str
    description: str
    func: Callable[..., Any]
    parameters: dict = field(default_factory=dict)

    def invoke(self, **kwargs) -> Any:
        return self.func(**kwargs)

    def __call__(self, **kwargs) -> Any:
        return self.invoke(**kwargs)


def build_cua_tools() -> list[Tool]:
    """Build a tool registry from cua-harness exports."""
    from cua_harness import (
        click,
        get_screen_size,
        get_window_state,
        launch_app,
        list_windows,
        press_key,
        screenshot,
        scroll,
        set_dry_run,
        type_text,
        wait_for,
    )

    return [
        Tool(
            name="launch_app",
            description="Launch a macOS application by bundle ID",
            func=launch_app,
            parameters={"bundle_id": "str", "urls": "list[str] | None"},
        ),
        Tool(
            name="list_windows",
            description="List all windows for a process",
            func=list_windows,
            parameters={"pid": "int"},
        ),
        Tool(
            name="get_window_state",
            description="Get accessibility tree and/or screenshot of a window",
            func=get_window_state,
            parameters={"pid": "int", "window_id": "int | None", "capture_mode": "str"},
        ),
        Tool(
            name="click",
            description="Click an element by index or coordinates",
            func=click,
            parameters={"pid": "int", "element_index": "int | None", "x": "float | None", "y": "float | None"},
        ),
        Tool(
            name="type_text",
            description="Type text into the focused element",
            func=type_text,
            parameters={"pid": "int", "text": "str"},
        ),
        Tool(
            name="press_key",
            description="Press a keyboard key with optional modifiers",
            func=press_key,
            parameters={"pid": "int", "key": "str", "modifiers": "list[str] | None"},
        ),
        Tool(
            name="scroll",
            description="Scroll in a direction",
            func=scroll,
            parameters={"pid": "int", "direction": "str", "amount": "int"},
        ),
        Tool(
            name="screenshot",
            description="Take a screenshot of a window",
            func=screenshot,
            parameters={"pid": "int", "window_id": "int | None"},
        ),
        Tool(
            name="get_screen_size",
            description="Get screen dimensions, optionally for a specific display",
            func=get_screen_size,
            parameters={"display_id": "int | None"},
        ),
        Tool(
            name="wait_for",
            description="Poll until a condition is met",
            func=wait_for,
            parameters={"predicate": "callable", "timeout": "float", "poll_interval": "float"},
        ),
        Tool(
            name="set_dry_run",
            description="Enable/disable dry-run mode (mutations are logged, not executed)",
            func=set_dry_run,
            parameters={"enabled": "bool"},
        ),
    ]


# --- Example agent loop ---

def agent_loop(task: str, bundle_id: str = "com.apple.TextEdit"):
    """
    Simulated agent loop that selects tools based on a task description.
    In a real framework, the LLM would do tool selection.
    """
    from cua_harness import ensure_daemon, set_dry_run

    ensure_daemon()
    set_dry_run(True)  # safe by default

    tools = {t.name: t for t in build_cua_tools()}
    print(f"Agent started with {len(tools)} tools available")
    print(f"Task: {task}")
    print(f"Tools: {', '.join(tools.keys())}")

    # Simulate tool calls an LLM agent would make
    app = tools["launch_app"](bundle_id=bundle_id)
    print(f"  launch_app → {app}")

    screen = tools["get_screen_size"]()
    print(f"  get_screen_size → {screen}")

    print("\nAgent loop complete (dry-run mode).")


if __name__ == "__main__":
    agent_loop("Open TextEdit and type a greeting")
