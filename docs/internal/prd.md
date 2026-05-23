# cua-harness PRD

> 与 `product-design.md` 互补：本文为正式产品需求，列用户故事、验收标准、范围边界。
> 决策叙事与价值主张见 `product-design.md`。

## 1. 背景

LLM agent 需要驱动 macOS 原生应用，但 `cua-driver` 仅提供 Rust CLI，每次调用需手写 `cua-driver call <tool> <json>`。agent 框架重复造轮子封装 subprocess、daemon 生命周期、临时文件管理。

## 2. 目标

| ID | 目标 | 衡量 |
|---|---|---|
| G1 | 单文件 helper 命名空间，零 import 即用 | heredoc 内直接 `click(...)` |
| G2 | 守护进程冷启自动化 | 用户代码无需感知 daemon |
| G3 | 22 helper 覆盖 cua-driver 全部 tool | 与 cua-driver tool registry 一一对应 |
| G4 | 与 browser-harness 行为同构 | 同一 agent 框架可同时挂载 |

## 3. 用户故事

### US-1 LLM agent 驱动桌面

**As** Claude Code agent
**I want** 在 heredoc 内调用 `get_window_state(capture_mode='som')` 拿到带标注截图与坐标
**So that** 视觉模型能输出 `click_id=12` 完成点击

**验收**：
- 单次调用返回 JSON，含 `screenshot_b64` + `elements[]`
- p50 < 500ms（10 寸 Retina 全屏 Safari）
- 元素编号稳定（连续 2 次同窗口 ID 不漂）

### US-2 自动化工程师写巡检脚本

**As** 自动化工程师
**I want** Python 脚本里直接 `for w in list_windows(): screenshot(...)` 巡检
**So that** 不用学 AppleScript 也能跨 app 操作

**验收**：
- `list_windows()` 返回所有可见窗口（pid + title + bounds）
- `screenshot(window_id=...)` 落盘 PNG，路径自管理
- 24h 跑 1000 次 click 失败率 < 1%

### US-3 新装用户

**As** 新用户
**I want** `cua-harness --doctor` 一次告诉我所有缺失项
**So that** 不用看 README 翻 TCC 流程

**验收**：
- 检查项：cua-driver 安装、daemon 可启、Accessibility 已授权
- 缺失项给出可复制的修复命令
- 一次通过率 ≥ 80%（dogfood 数据）

### US-4 调试

**As** 维护者
**I want** `cua-harness --reload` 重启 daemon
**So that** daemon 卡死时不用 kill -9

**验收**：
- `--reload` 等价 `cua-driver kill && ensure_daemon()`
- 5s 内回到可用状态

## 4. 功能范围

### 4.1 In Scope

- 22 helper（详见 `technical-design.md` §4）
- 4 种 `capture_mode`：som / ax / vision / screenshot
- daemon 自启与健康检查
- `--doctor` / `--reload` / `--version` CLI 子命令
- heredoc namespace exec 入口

### 4.2 Out of Scope

| 不做 | 原因 |
|---|---|
| 浏览器自动化 | 用 browser-harness |
| Linux/Windows | 仅 macOS（cua-driver 限制）|
| 重试/规划/记忆 | 上层 agent 职责 |
| 云端托管 | 保持本地、open |
| 内置 LLM 调用 | 与模型解耦 |
| 录制/回放 | 0.3.0 视反馈再定 |

## 5. 非功能需求

| 维度 | 要求 |
|---|---|
| 性能 | `get_window_state(som)` p50 < 500ms |
| 体积 | 安装 < 200KB（不含 cua-driver）|
| 稳定 | 24h 1000 次 click 失败率 < 1% |
| 启动 | daemon 冷启 ≤ 5s |
| 学习 | 22 helper 上手 < 10min（看 SKILL.md）|

## 6. 发布门控

| 版本 | 准入条件 |
|---|---|
| 0.1.0 | P0 三项修完（详见 `technical-design.md` §9）；pytest 通过；TCC 流程文档化 |
| 0.1.1 | P1/P2 三项修完；内部 dogfood 1 周无回归 |
| 0.2.0 | 至少 1 个外部 agent 框架接入；`wait_for` / 多显示器 / AX diff 三选二落地 |

## 7. 依赖与风险

| 依赖 | 风险 | 缓解 |
|---|---|---|
| cua-driver | 上游停滞 | 薄封装，可换底层 |
| macOS Accessibility API | OS 升级破坏 | 跟随 cua-driver upstream |
| TCC 授权流程 | 用户放弃 | doctor 给操作指引 |
| LLM 误操作 | 数据风险 | 文档明示责任，0.3.0 加 dry-run |

## 8. 文档交付

| 文档 | 受众 | 必备 |
|---|---|---|
| `README.md` | 所有人 | ✓ |
| `install.md` | 新装 | ✓ |
| `SKILL.md` | LLM | ✓ |
| `docs/prd.md`（本文）| 决策、PM | ✓ |
| `docs/spec.md` | 实现/QA | ✓ |
| `docs/tsd.md` | 维护、贡献者 | ✓ |
| `docs/product-design.md` | 决策叙事 | ✓ |
| `docs/technical-design.md` | 架构概览 | ✓ |
