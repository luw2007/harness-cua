# cua-harness 技术方案

## 1. 定位

Python SDK，将 `cua-driver`（Rust 守护进程）暴露为 LLM agent 可直接调用的函数。支持两种使用模式：heredoc namespace exec（零 import）和标准 Python import（可测试、IDE 补全）。

不做：浏览器/UI 自动化框架、状态管理、重试策略、并发调度。

## 2. 架构分层

```
┌──────────────────────────────────────────────┐
│  agent code                                   │
│    - heredoc stdin (零 import)                │
│    - from cua_harness import * (标准 import)  │
├──────────────────────────────────────────────┤
│  cua_harness.run.main()                       │
│    - parse args (--version/--doctor/--reload) │
│    - ensure_daemon()                          │
│    - _build_namespace() 注入全部 helpers      │
│    - exec(compile(stdin)) + traceback         │
├──────────────────────────────────────────────┤
│  cua_harness.helpers (32 个函数)              │
│    └── _cua(tool, **kwargs)                   │
├──────────────────────────────────────────────┤
│  cua_harness.client.CuaClient                 │
│    └── Unix socket (line-delimited JSON)      │
│    └── 持久连接，自动重连                      │
├──────────────────────────────────────────────┤
│  cua-driver daemon                            │
│  ~/Library/Caches/cua-driver/cua-driver.sock  │
│    └── macOS AX / CoreGraphics / TCC          │
└──────────────────────────────────────────────┘
```

## 3. IPC 契约

直接 Unix socket 通信，line-delimited JSON 协议：

**请求格式**：
```json
{"method":"call","name":"<tool_name>","args":{...}}
{"method":"list"}
{"method":"describe","name":"<tool_name>"}
{"method":"shutdown"}
```

**响应格式**：
```json
{"ok":true,"result":{...}}
{"ok":false,"error":"...","exitCode":64|65|70|1}
```

- 持久连接复用，无 subprocess fork 开销
- 超时：30s（call）/ 5s（alive check）
- 连接断开自动重连
- daemon 返回 `ok:false` 时抛 `RuntimeError`

## 4. Helpers 目录（32 个）

| 类别 | helpers |
|---|---|
| 守护进程 | `daemon_alive`, `ensure_daemon`, `check_permissions` |
| 应用 | `launch_app`, `list_apps`（别名 `app_info`）|
| 窗口 | `list_windows`, `get_window_state` |
| 鼠标 | `click`, `double_click`, `right_click`, `drag`, `move_cursor`, `get_cursor_position` |
| 键盘 | `type_text`, `set_value`, `press_key`, `hotkey` |
| 滚动/缩放 | `scroll`, `zoom`, `page` |
| 屏幕 | `screenshot`, `get_screen_size` |
| 配置 | `get_config`, `set_config` |
| 录制 | `set_recording`, `get_recording_state`, `replay_trajectory` |
| 光标 | `set_agent_cursor_enabled`, `get_agent_cursor_state` |

## 5. 采集模式

| mode | screenshot | AX tree | 用途 |
|---|---|---|---|
| `som` | 内嵌带标注 | ✗ | LLM 视觉点击（默认推荐）|
| `ax` | ✗ | ✓ | 文本式 UI 推理，零图像 token |
| `vision` | 原图 | ✓ | 双通道融合 |
| `screenshot` | 原图 | ✗ | 纯视觉 |

`vision` 与 `screenshot` 通过 `_tmp_png()` 申请临时文件，文件以 `screenshot_out_file` 参数传给 daemon，daemon 写入 PNG 字节。

临时文件在进程退出时由 `atexit` hook 统一清理。

## 6. 守护进程生命周期

`ensure_daemon()`：
1. `CuaClient.alive()` 尝试 socket connect + `{"method":"list"}`，5s 超时
2. 不存活则 `Popen(["cua-driver", "serve"], stderr=PIPE)`
3. 20×0.25s = 5s 轮询 `alive()`
4. 超时抛 `RuntimeError`，附带 stderr 内容

首次拉起守护进程会触发 macOS Accessibility TCC 弹窗。授权前所有 AX 调用失败。

## 7. 使用模式

### heredoc exec（向后兼容）

```bash
cua-harness <<'PY'
state = get_window_state(pid)
click(pid, element_index=3)
PY
```

`run.main()` 读 stdin，注入全部 helpers 到 namespace，exec 执行。异常由 `try/except` 捕获，打印完整 traceback 到 stderr。

### 标准 import（推荐新项目）

```python
from cua_harness import ensure_daemon, get_window_state, click
ensure_daemon()
state = get_window_state(pid)
```

可测试、IDE 补全、可调试。`__all__` 导出 32 个公开符号。

## 8. 错误模型

策略：薄封装、不吞错、不重试。

- daemon 返回 `ok:false` → 抛 `RuntimeError(error_message)`
- socket 连接失败 → 抛 `ConnectionError`
- agent 代码异常 → `traceback.print_exc()` + `sys.exit(1)`
- `_load_agent_helpers` 失败 → 打印 warning 继续执行

不做：自动重试、TCC 检测、daemon 自愈。

## 9. 与 browser-harness 对照

| 维度 | browser-harness | cua-harness |
|---|---|---|
| 后端 | Playwright (Chromium) | cua-driver (macOS AX) |
| IPC | Python ↔ Playwright（同进程）| Python → Unix socket → Rust daemon |
| 连接 | 同进程 | 持久 socket，复用跨调用 |
| 元素定位 | CSS / role / text | AX role+title / 像素坐标 / SOM 标注 |
| 视觉模式 | DOM-only / screenshot / SOM | ax / screenshot / som / vision |
| 状态 | page.context | 全局桌面 |
| 跨进程 | 否（单 page）| 是（任意 app）|

## 10. 测试与验证

- 单元：`pytest`，集中在 `CuaClient` 协议、`_cua` 参数构造
- 集成：依赖真实 cua-driver + TCC 授权，CI 不跑
- lint：`ruff check`
- import 验证：`python -c "from cua_harness import *"`

## 11. 路线图

- **0.2.0**（当前）：socket IPC、声明式 tool 注册、lib 化入口、32 tool 覆盖
- **0.3.0**：可选增量
  - `wait_for(predicate, timeout)` helper
  - 多显示器 `get_screen_size(display_id)`
  - AX tree diff（前后两次 `get_window_state` 自动 diff）
  - async 版本 `AsyncCuaClient`
