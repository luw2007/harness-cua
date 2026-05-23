"""cua-harness: agent-friendly heredoc CLI for cua-driver desktop automation."""

__version__ = "0.1.0"

USAGE = """\
Usage: cua-harness <<'PY'
  # Python code with pre-imported helpers
  state = get_window_state(pid)
  click(pid, element_index=3)
PY

Subcommands:
  --version   Print version
  --doctor    Check cua-driver availability and permissions
  --reload    Reload agent_helpers.py
"""
