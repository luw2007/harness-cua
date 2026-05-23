# cua-harness 功能规范

> 实现/QA 用。逐 helper 行为契约、参数约束、错误条件。
> 架构概览见 `technical-design.md`，IPC 字节级契约见 `tsd.md`。

## 1. 入口

### 1.1 CLI

```
cua-harness [--doctor | --reload | --version]
```

| flag | 行为 | 退出码 |
|---|---|---|
| 无 | 读 stdin，注入 22 helper，`exec` | 0=成功；非 0=用户代码异常 |
| `--doctor` | 检查 cua-driver / daemon / TCC | 0=全绿；1=缺失项 |
| `--reload` | `cua-driver kill` + `ensure_daemon()` | 0=已就绪；1=拉起失败 |
| `--version` | 打印版本 | 0 |

### 1.2 命名空间

stdin 代码可直接引用 22 helper 与 `__name__ == "__main__"`，无需 import。`agent-workspace/agent_helpers.py` 可扩展。

## 2. Helper 契约

参数全部 keyword 形式；返回 dict（除 `daemon_alive` 返回 bool）。

### 2.1 守护进程

| helper | 参数 | 返回 | 失败条件 |
|---|---|---|---|
| `daemon_alive()` | — | `bool` | socket 不存在/无响应 → `False` |
| `ensure_daemon()` | — | `dict{success}` | 5s 内未起 → `RuntimeError` |
| `check_permissions()` | — | `dict{accessibility, screen_recording}` | 未授权字段为 `false` |

### 2.2 应用

| helper | 参数 | 返回 | 备注 |
|---|---|---|---|
| `launch_app(bundle_id\|name)` | 二选一 | `dict{pid}` | 已运行则前置 |
| `app_info()` | — | `dict{apps:[...]}` | 别名 `list_apps`（见 §6 已知问题）|

### 2.3 窗口

| helper | 参数 | 返回 |
|---|---|---|
| `list_windows()` | — | `dict{windows:[{id,pid,title,bounds}]}` |
| `get_window_state(window_id?, capture_mode='som')` | mode ∈ {som,ax,vision,screenshot} | 见 §3 |

### 2.4 鼠标

| helper | 参数 | 行为 |
|---|---|---|
| `click(x,y\|element_id)` | 坐标或 SOM 编号 | 单击 |
| `double_click(x,y)` | | 双击 |
| `right_click(x,y)` | | 右键 |
| `drag(from_x,from_y,to_x,to_y,duration?)` | duration 默认 0.5s | 按下→移动→释放 |
| `move_cursor(x,y)` | | 仅移动 |
| `get_cursor_position()` | — | `dict{x,y}` |

### 2.5 键盘

| helper | 参数 | 行为 |
|---|---|---|
| `type_text(text)` | UTF-8 字符串 | 逐字符输入 |
| `set_value(element_id,value)` | AX 元素 | 直接设值（不走输入法）|
| `press_key(key)` | 单键名 | 按下释放 |
| `hotkey(*keys)` | 修饰键序列 | `hotkey('cmd','b')` |

### 2.6 滚动 / 缩放

| helper | 参数 |
|---|---|
| `scroll(x,y,delta_x,delta_y)` | 像素 |
| `zoom(x,y,scale)` | scale > 1 放大 |
| `page(x,y,direction)` | direction ∈ {up,down} |

### 2.7 屏幕

| helper | 参数 | 返回 |
|---|---|---|
| `screenshot(out_path?, window_id?)` | | `dict{path}` |
| `get_screen_size()` | — | `dict{width,height}` |

## 3. 采集模式

`get_window_state(capture_mode=...)` 返回字段：

| mode | screenshot_b64 | elements | ax_tree | 用途 |
|---|---|---|---|---|
| `som` | ✓（带编号标注）| ✓（含 id↔坐标）| ✗ | 视觉 LLM 默认 |
| `ax` | ✗ | ✗ | ✓ | 文本推理，零图像 token |
| `vision` | ✓（原图）| ✗ | ✓ | 双通道融合 |
| `screenshot` | ✗ | ✗ | ✗ | 仅落盘 PNG |

`vision` 与 `screenshot` 的 PNG 通过临时文件传递，调用方收到 `path` 字段。

## 4. 错误模型

| 来源 | 表现 | 处理 |
|---|---|---|
| subprocess 退出非 0 | `CalledProcessError` | 直接冒泡 |
| stdout 非 JSON | 退化 `{success:True, raw:stdout}` | **0.1.0 改 raise**（P0-1）|
| daemon 未起 | `RuntimeError("daemon failed to start in 5s")` | 用户 `--reload` |
| TCC 未授权 | AX 调用返回 `success:False` + `error` | doctor 提示 |
| agent 代码异常 | `exec` 抛出 → 进程退出非 0 | **0.1.1 加 traceback**（P1-4）|

## 5. 临时文件

PNG 临时路径形如 `$TMPDIR/cua-harness-<uuid>.png`。

**当前**：永不清理（P0-2）。
**0.1.0**：`tempfile.NamedTemporaryFile(delete=False)` + `atexit` 清理。

## 6. 已知偏差（vs 本规范）

引用 `technical-design.md` §9：

| ID | 现象 | 修复版本 |
|---|---|---|
| P0-1 | JSON 解析失败静默成功 | 0.1.0 |
| P0-2 | 临时 PNG 泄漏 | 0.1.0 |
| P0-3 | `ensure_daemon` 吞 stderr | 0.1.0 |
| P1-4 | `exec` 异常无栈 | 0.1.1 |
| P1-5 | `_load_agent_helpers` 无兜底 | 0.1.1 |
| P2-6 | `app_info` 命名不一致 | 0.1.1 |

## 7. 兼容性

- Python ≥ 3.10
- macOS ≥ 13（cua-driver 要求）
- cua-driver ≥ 与 helper tool registry 对齐版本（pinned in `pyproject.toml`）

## 8. 测试矩阵

| 层级 | 工具 | 范围 | CI |
|---|---|---|---|
| 单元 | pytest | `_cua` 命令构造、`_tmp_png` 路径 | ✓ |
| 集成 | pytest + 真实 cua-driver | 22 helper 端到端 | ✗（需 TCC）|
| lint | ruff | 全部 .py | ✓（pre-commit）|
| 手测 | `agent-workspace/agent_helpers.py` | 视觉/AX 双通道抽样 | ✗ |
