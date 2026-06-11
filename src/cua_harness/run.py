"""Entry point: read stdin heredoc, ensure daemon, exec code."""

import importlib.util
import sys
import traceback
from pathlib import Path

import cua_harness
from cua_harness import USAGE, __all__, __version__
from cua_harness.client import ensure_daemon, kill_daemon
from cua_harness.helpers import AGENT_WORKSPACE, load_app_skills


def _load_all_app_skills(ns: dict) -> None:
    skills_root = AGENT_WORKSPACE / "app-skills"
    if not skills_root.is_dir():
        return
    for entry in sorted(skills_root.iterdir()):
        if entry.is_dir() and (entry / "helpers.py").exists():
            try:
                load_app_skills(entry.name, ns)
            except Exception as e:
                print(f"Warning: failed to load app-skill {entry.name}: {e}", file=sys.stderr)


def _load_agent_helpers(ns: dict) -> None:
    workspace = Path.cwd() / "agent-workspace"
    helper_file = workspace / "agent_helpers.py"
    if not helper_file.exists():
        return
    try:
        spec = importlib.util.spec_from_file_location("agent_helpers", helper_file)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for name in dir(mod):
            if not name.startswith("_"):
                ns[name] = getattr(mod, name)
    except Exception as e:
        print(f"Warning: failed to load agent_helpers.py: {e}", file=sys.stderr)


def _doctor() -> None:
    print(f"cua-harness {__version__}")
    print()
    import subprocess
    try:
        result = subprocess.run(
            ["cua-driver", "doctor"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        print(result.stdout.strip() if result.stdout else result.stderr.strip())
        if result.returncode != 0:
            sys.exit(1)
    except subprocess.TimeoutExpired:
        print("cua-driver doctor timed out — daemon likely not running.")
        print("Start daemon with: cua-driver serve")
        sys.exit(1)
    except FileNotFoundError:
        print("cua-driver not found. Install: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/trycua/cua/main/libs/cua-driver/scripts/install.sh)\"")
        sys.exit(1)


def _build_namespace() -> dict:
    ns: dict = {"__builtins__": __builtins__}
    for name in __all__:
        ns[name] = getattr(cua_harness, name)
    return ns


def main() -> None:
    args = sys.argv[1:]

    if "--version" in args:
        print(f"cua-harness {__version__}")
        return

    if "--doctor" in args:
        _doctor()
        return

    if "--help" in args or "-h" in args:
        print(USAGE)
        return

    if "--reload" in args:
        kill_daemon()
        ensure_daemon()
        print("Daemon restarted.")
        return

    if sys.stdin.isatty():
        print(USAGE, file=sys.stderr)
        sys.exit(1)

    code = sys.stdin.read()
    if not code.strip():
        return

    ensure_daemon()

    ns = _build_namespace()
    _load_agent_helpers(ns)
    _load_all_app_skills(ns)

    try:
        exec(compile(code, "<stdin>", "exec"), ns)
    except Exception:
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
