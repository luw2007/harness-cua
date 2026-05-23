# cua-harness 技术方案

## 1. 定位

Python 薄封装层，将 `cua-driver`（Rust 守护进程 + CLI）暴露为 LLM agent 可直接调用的命名空间式 helpers。设计参考 `browser-harness`：单文件 helper、heredoc namespace exec、最少抽象。

不做：浏览器/UI 自动化框架、状态管理、重试策略、并发调度。

## 2. 架构分层

```
┌──────────────────────────────────────────────┐
│  agent code (heredoc 输入 stdin)              │
├──────────────────────────────────────────────┤
│  cua_harness.run.main()                       │
│    - parse args (--version/--doctor/--reload) │
│    - ensure_daemon()                          │
│    - 注入 22 helpers 到 ns                    │
│    - exec(compile(stdin, "<stdin>", "exec"))  │
├──────────────────────────────────────────────┤
│  cua_harness.helpers (22 个函数)              │
│    └── _cua(tool, **kwargs)                   │
├──────────────────────────────────────────────┤
│  subprocess: cua-driver call <tool> <json>    │
│    --compact [--screenshot-out-file <path>]   │
├──────────────────────────────────────────────┤
│  Unix socket                                  │
│  ~/Library/Caches/cua-driver/cua-driver.sock  │
├──────────────────────────────────────────────┤
│  cua-driver daemon (Rust)                     │
│    └── macOS AX / CoreGraphics / TCC          │
└──────────────────────────────────────────────┘
```

## 3. IPC 契约

CLI 调用统一形态：

```
cua-driver call <tool-snake_case> [<json-args>] --compact [--screenshot-out-file <path>]
```

- 工具名 snake_case，与 cua-driver 内部 tool registry 对齐
- 参数以单个 JSON 对象传递；无参时省略
- `--compact`：紧凑 JSON 输出
- `--screenshot-out-file`：仅 `vision` / `screenshot` 模式需要，路径为临时 PNG

返回：stdout JSON。`_cua` 调用 `json.loads`；解析失败回退 `{"success": True, "raw": stdout}`（已知问题，见 §9）。

超时：30s（call）/ 5s（status）/ 15s（doctor）。

## 4. Helpers 目录（22 个）

| 类别 | helpers |
|---|---|
| 守护进程 | `daemon_alive`, `ensure_daemon`, `check_permissions` |
| 应用 | `launch_app`, `app_info`（→ `list_apps`）|
| 窗口 | `list_windows`, `get_window_state` |
| 鼠标 | `click`, `double_click`, `right_click`, `drag`, `move_cursor`, `get_cursor_position` |
| 键盘 | `type_text`, `set_value`, `press_key`, `hotkey` |
| 滚动/缩放 | `scroll`, `zoom`, `page` |
| 屏幕 | `screenshot`, `get_screen_size` |

`get_window_state(capture_mode)` 是核心入口，决定四种采集模式。

## 5. 采集模式

| mode | screenshot | AX tree | 用途 |
|---|---|---|---|
| `som` | 内嵌带标注 | ✗ | LLM 视觉点击（默认推荐）|
| `ax` | ✗ | ✓ | 文本式 UI 推理，零图像 token |
| `vision` | 原图 | ✓ | 双通道融合 |
| `screenshot` | 原图 | ✗ | 纯视觉 |

`vision` 与 `screenshot` 通过 `_tmp_png()` 申请临时文件并以 `--screenshot-out-file` 落盘。

## 6. 守护进程生命周期

`ensure_daemon()`：
1. `daemon_alive()` 调 `cua-driver status`，5s 超时
2. 不存活则 `Popen(["cua-driver", "serve"], stdout=DEVNULL, stderr=DEVNULL)`
3. 20×0.25s = 5s 轮询 `daemon_alive()`
4. 超时抛 `RuntimeError`

首次拉起守护进程会触发 macOS Accessibility TCC 弹窗。授权前所有 AX 调用失败。

`--reload` 等价于 `cua-driver kill && ensure_daemon()`。

## 7. heredoc namespace exec

`run.main()` 末尾：

```python
ns = {h.__name__: h for h in HELPERS}
ns["__name__"] = "__main__"
code = sys.stdin.read()
exec(compile(code, "<stdin>", "exec"), ns)
```

agent 在 stdin 写 Python，自然引用 `click(...)` / `get_window_state(...)`，无需 import。与 browser-harness 同构。

## 8. 错误模型

当前策略：薄封装、不吞错、不重试。

- subprocess 失败 → `CalledProcessError` 直接冒泡
- JSON 解析失败 → 退化为 `{"success": True, "raw": stdout}`（**与"不吞错"原则冲突**，见 §9 已知问题）
- agent 代码异常 → `exec` 抛出栈，由 shell 捕获

不做：自动重试、TCC 检测、daemon 自愈。

## 9. 已知问题与路线图

详见 `.claude/implementation-notes.md` 内联评审。

| ID | 严重度 | 位置 | 现象 | 修复 |
|---|---|---|---|---|
| 1 | P0 | `helpers.py:31-34` | `_cua` 把 `JSONDecodeError` 静默成 `success=True` | raise `RuntimeError(stdout)` |
| 2 | P0 | `helpers.py:39-43` | `_tmp_png` 临时 PNG 永不清理 | 改 `tempfile.NamedTemporaryFile(delete=False)` + 退出钩子 / 上层 `finally` |
| 3 | P0 | `helpers.py:58-70` | `ensure_daemon` 吞 stderr、无 TCC 等待、无重启 | 保留 stderr，5s 后若仍未起则打印 stderr |
| 4 | P1 | `run.py:122` | `exec` 无 try/except，agent 异常无栈定位 | 包 `try/except` 打印 `traceback.format_exc()` 到 stderr |
| 5 | P1 | `run.py:34-44` | `_load_agent_helpers` 无 try/except | 加入 `ImportError` 兜底 |
| 6 | P2 | `helpers.py:271-272` | `app_info` 名称与底层 `list_apps` 不一致 | 改名为 `list_apps` 或在 docstring 注明别名 |

路线图：

- **0.1.0**：当前 + 修 P0（Issue 1/2/3）
- **0.1.1**：修 P1/P2（Issue 4/5/6）
- **0.2.0**：可选增量
  - `wait_for(predicate, timeout)` helper
  - 多显示器 `get_screen_size(display_id)`
  - AX tree diff（前后两次 `get_window_state` 自动 diff）

## 10. 与 browser-harness 对照

| 维度 | browser-harness | cua-harness |
|---|---|---|
| 后端 | Playwright (Chromium) | cua-driver (macOS AX) |
| IPC | Python ↔ Playwright（同进程）| subprocess → Rust daemon → Unix socket |
| 元素定位 | CSS / role / text | AX role+title / 像素坐标 / SOM 标注 |
| 视觉模式 | DOM-only / screenshot / SOM | ax / screenshot / som / vision |
| 状态 | page.context | 全局桌面 |
| 跨进程 | 否（单 page）| 是（任意 app）|

## 11. 测试与验证

- 单元：`pytest`，集中在 `_cua` 命令构造、`_tmp_png` 路径
- 集成：依赖真实 cua-driver + TCC 授权，CI 不跑
- lint：`ruff check`，pre-commit 已配
- 手测脚本：`agent-workspace/agent_helpers.py`
