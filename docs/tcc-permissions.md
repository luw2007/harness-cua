# TCC Permissions for cua-driver

macOS requires Transparency, Consent, and Control (TCC) grants before cua-driver can observe or control the desktop.

## Required Permissions

| Permission | TCC Service | Why |
|---|---|---|
| Accessibility | `kTCCServiceAccessibility` | Read AX tree, synthetic clicks/keys |
| Screen Recording | `kTCCServiceScreenCapture` | Screenshot capture |

## Grant Flow

### 1. Check current status

```bash
cua-driver doctor
# or programmatically:
cua-harness --doctor
```

`check_permissions` returns per-permission granted/denied:

```python
from cua_harness.helpers import check_permissions
print(check_permissions())
# {"accessibility": true, "screen_recording": false}
```

### 2. Trigger system prompt (first run)

On first `cua-driver serve`, macOS shows a TCC dialog for each missing permission.
The user must manually click "Allow" in System Settings.

Path: **System Settings → Privacy & Security → Accessibility / Screen Recording**

Add the terminal app (Terminal.app, iTerm2, etc.) or the `cua-driver` binary.

### 3. Verify after granting

```bash
cua-driver doctor
# All checks should pass
```

### 4. Headless / CI environments

TCC cannot be granted interactively in headless CI. Options:

- **MDM profile**: Deploy a TCC configuration profile via Jamf/Mosyle that pre-approves the binary.
- **tccutil** (dev only): `tccutil reset Accessibility` resets; cannot grant programmatically on modern macOS.
- **VM with GUI**: Use a macOS VM where TCC prompts can be accepted during setup.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ensure_daemon` starts but `get_window_state` returns empty | Screen Recording not granted | Grant in System Settings |
| `click` has no effect | Accessibility not granted | Grant in System Settings |
| Permission was granted but stopped working | macOS revoked after app update | Re-grant in System Settings |

## Reset permissions (development)

```bash
tccutil reset Accessibility com.example.cua-driver
tccutil reset ScreenCapture com.example.cua-driver
```

Replace `com.example.cua-driver` with the actual bundle identifier or binary path.
