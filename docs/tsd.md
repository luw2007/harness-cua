# cua-harness Technical Specification Document

> 字节级契约：subprocess 调用、JSON schema、退出码、文件路径、环境变量。
> 高层架构见 `technical-design.md`，行为契约见 `spec.md`。

## 1. 进程模型

```
parent (agent shell)
  └── cua-harness (python, run.main)
        ├── subprocess: cua-driver call <tool> --compact
        └── subprocess: cua-driver status / serve / kill
              └── daemon (rust, long-lived, Unix socket)
```

`cua-harness` 与 `cua-driver` daemon 之间无直接 socket 通信；所有调用经由 `cua-driver call` CLI。

## 2. 文件路径

| 路径 | 用途 | 生命周期 |
|---|---|---|
| `~/Library/Caches/cua-driver/cua-driver.sock` | daemon Unix socket | daemon 存活期 |
| `~/Library/Caches/cua-driver/cua-driver.pid` | daemon PID | daemon 存活期 |
| `$TMPDIR/cua-harness-<uuid>.png` | 截图临时文件 | 0.1.0 起 atexit 清理 |
| `~/.cua-harness/agent_helpers.py`（可选）| 用户扩展 helper | 永久 |

## 3. 子进程调用规范

### 3.1 通用形态

```
cua-driver call <tool-snake_case> [<json-args>] --compact [--screenshot-out-file <path>]
```

| 参数 | 必需 | 说明 |
|---|---|---|
| `<tool-snake_case>` | ✓ | 与 cua-driver tool registry 对齐；snake_case |
| `<json-args>` | 视 tool | 单个 JSON 对象；无参省略 |
| `--compact` | ✓ | 紧凑 JSON（无空白）|
| `--screenshot-out-file` | 仅 vision/screenshot | 绝对路径 |

### 3.2 超时

| 子命令 | 超时 |
|---|---|
| `cua-driver call <tool>` | 30s |
| `cua-driver status` | 5s |
| `cua-driver --doctor` 内部检查 | 15s 总 |

### 3.3 stdout 解析

```python
def _cua(tool, **kwargs):
    out = subprocess.check_output([...], timeout=30)
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        # 0.1.0 改：raise RuntimeError(f"non-JSON stdout: {out!r}")
        return {"success": True, "raw": out.decode()}
```

## 4. JSON Schema

### 4.1 通用响应

```json
{
  "success": true | false,
  "error": "string (optional, 仅 success=false)",
  "data": "..."
}
```

### 4.2 `get_window_state` 响应

```json
{
  "success": true,
  "window": {"id": int, "pid": int, "title": str, "bounds": {"x":..,"y":..,"w":..,"h":..}},
  "capture_mode": "som" | "ax" | "vision" | "screenshot",
  "screenshot_b64": "string | null",
  "screenshot_path": "string | null",
  "ax_tree": {...} | null,
  "elements": [
    {"id": int, "role": str, "title": str, "bounds": {...}}
  ] | null
}
```

| mode | screenshot_b64 | screenshot_path | ax_tree | elements |
|---|---|---|---|---|
| som | ✓（含标注）| null | null | ✓ |
| ax | null | null | ✓ | null |
| vision | null | ✓ | ✓ | null |
| screenshot | null | ✓ | null | null |

### 4.3 `list_windows` 响应

```json
{
  "success": true,
  "windows": [
    {"id": int, "pid": int, "title": str, "bounds": {...}, "app": str}
  ]
}
```

### 4.4 `check_permissions` 响应

```json
{
  "success": true,
  "accessibility": true | false,
  "screen_recording": true | false
}
```

## 5. 退出码

| 进程 | 码 | 含义 |
|---|---|---|
| `cua-harness` | 0 | stdin 代码正常结束 |
| | 1 | doctor 检查不通过 / `--reload` 失败 |
| | 非 0（其他）| stdin 代码异常（exec 冒泡）|
| `cua-driver call` | 0 | tool 执行成功（含 `success:false` 业务失败）|
| | 非 0 | CLI 自身错误（参数、daemon 不可达）|

`success:false` 不映射退出码；调用方按 JSON 字段判断。

## 6. 环境变量

| 变量 | 默认 | 用途 |
|---|---|---|
| `CUA_DRIVER_BIN` | `cua-driver` | CLI 路径 |
| `CUA_DRIVER_SOCK` | `~/Library/Caches/cua-driver/cua-driver.sock` | socket 覆写（调试）|
| `CUA_HARNESS_TMPDIR` | `$TMPDIR` | 截图临时目录 |

## 7. daemon 生命周期状态机

```
        ┌──────────┐
   ┌───►│  ABSENT  │ (socket 不存在)
   │    └────┬─────┘
   │         │ ensure_daemon → Popen serve
   │         ▼
   │    ┌──────────┐
   │    │ STARTING │ (≤ 5s 轮询)
   │    └────┬─────┘
   │         │ status 200
   │         ▼
   │    ┌──────────┐
   └────┤  ALIVE   │
 kill   └──────────┘
```

| 转移 | 触发 | 超时 |
|---|---|---|
| ABSENT → STARTING | `Popen(["cua-driver","serve"])` | — |
| STARTING → ALIVE | `cua-driver status` 返回 0 | 5s（20×0.25s 轮询）|
| STARTING → ABSENT | 5s 超时 | `RuntimeError` |
| ALIVE → ABSENT | `cua-driver kill` 或 daemon 崩溃 | — |

## 8. heredoc exec 协议

```python
# run.main() 末尾
ns = {h.__name__: h for h in HELPERS}
ns["__name__"] = "__main__"
ns.update(_load_agent_helpers())  # 可选
code = sys.stdin.read()
exec(compile(code, "<stdin>", "exec"), ns)
# 0.1.1：包 try/except 打 traceback 到 stderr
```

stdin 字符集：UTF-8。
stdout：用户代码自由写。
stderr：daemon 启动日志（0.1.0 起保留）+ traceback（0.1.1 起）。

## 9. 兼容性矩阵

| 组件 | 最低 | 推荐 |
|---|---|---|
| Python | 3.10 | 3.12 |
| macOS | 13 (Ventura) | 14+ |
| cua-driver | pinned in `pyproject.toml` | latest |

## 10. 安全约束

- 不通过 stdin 接受不可信代码（heredoc exec 默认信任调用方）
- 不解密/上传任何系统信息
- 截图临时文件权限 0600（atexit 清理后失效）
- TCC 授权一次永久，cua-harness 不缓存敏感数据

## 11. 性能预算

| 操作 | p50 | p99 |
|---|---|---|
| `_cua` subprocess overhead | < 50ms | < 150ms |
| `get_window_state(som)` 端到端 | < 500ms | < 1500ms |
| `get_window_state(ax)` 端到端 | < 200ms | < 800ms |
| `click(x,y)` | < 100ms | < 400ms |
| daemon 冷启 | < 3s | < 5s |

## 12. 版本契约

semver；MINOR 不破坏 helper 签名；MAJOR 允许重命名（如 P2-6 `app_info` → `list_apps` 计 0.2.0）。
