# Installation

## Prerequisites

1. **cua-driver** installed and on PATH:
   ```bash
   which cua-driver  # should resolve
   cua-driver status '{}'  # should respond
   ```

2. **macOS permissions** granted to cua-driver:
   - System Settings → Privacy & Security → Accessibility → enable cua-driver
   - System Settings → Privacy & Security → Screen Recording → enable cua-driver

3. **Python 3.11+** available

## Install

```bash
cd /path/to/harness-cua
uv tool install -e .
```

Verify:
```bash
cua-harness --version
cua-harness --doctor
```

## Register with Claude Code

Add to your Claude Code skill references:
```
@~/path/to/harness-cua/SKILL.md
```

## Troubleshooting

### `cua-driver: command not found`
Ensure cua-driver binary is on your PATH. Check with `which cua-driver`.

### Daemon won't start
```bash
cua-driver serve  # run manually to see errors
```

### Permission denied errors
Re-grant Accessibility and Screen Recording permissions in System Settings. You may need to remove and re-add the entry.

### `cua-harness --doctor` shows NOT granted
Open System Settings → Privacy & Security, toggle permissions off and on for cua-driver.
