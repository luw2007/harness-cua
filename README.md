# cua-harness

Agent-friendly heredoc CLI for desktop automation via [cua-driver](https://github.com/anthropics/cua-driver).

```bash
cua-harness <<'PY'
result = launch_app("com.apple.Safari")
pid = result["data"]["pid"]
state = get_window_state(pid, capture_mode="som")
click(pid, element_index=5)
PY
```

## Quick start

```bash
uv tool install -e .
cua-harness --doctor
```

See [install.md](install.md) for full setup and [SKILL.md](SKILL.md) for agent usage reference.
