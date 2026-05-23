# cua-harness 产品方案

## 1. 一句话定位

**给 LLM agent 的 macOS 桌面操作 SDK**：把 cua-driver 的 Rust CLI 封装成可 heredoc 调用的 Python 命名空间，让 agent 用 `click()` / `get_window_state()` 直接驱动任意 macOS 应用。

## 2. 目标用户

| 角色 | 场景 |
|---|---|
| LLM agent 框架（Claude Code / OpenAI Operator 等）| 在 macOS 本地驱动桌面应用完成任务 |
| 自动化工程师 | 写测试/巡检脚本，跨原生 app（非 web）|
| RPA 用户 | 替代 AppleScript / Automator，用自然语言/Python 描述流程 |

非目标用户：浏览器自动化（用 browser-harness）、跨平台（仅 macOS）、无人值守服务器（依赖 GUI）。

## 3. 核心使用场景

1. **跨 app 工作流**：从 Mail 抓附件 → Preview 标注 → 拖到 Slack 发送
2. **桌面 UI 巡检**：定期截图 + AX tree diff，监控特定窗口状态
3. **agent 工具调用**：LLM 在 chat 里说"打开 Xcode build"，agent 调 `launch_app` + `hotkey('cmd', 'b')`
4. **可视化点击**：`get_window_state(capture_mode='som')` 把元素编号送给视觉模型，模型回 `click_id=12`

## 4. 价值主张

### vs 直接用 cua-driver CLI

| 痛点 | cua-harness 解法 |
|---|---|
| 每次都拼 `cua-driver call ... --compact ...` | helper 函数封装 |
| JSON 参数手写易错 | Python kwargs |
| 守护进程冷启动逻辑要自己写 | `ensure_daemon()` 自动处理 |
| 截图临时文件管理 | `_tmp_png` + 自动 `--screenshot-out-file` |

### vs browser-harness

| 维度 | browser-harness | cua-harness |
|---|---|---|
| 范围 | 浏览器内 | 整个 macOS 桌面 |
| 跨原生 app | 否 | 是 |
| 部署 | 跨平台 | 仅 macOS |

二者互补，可同 agent 同时引入。

### vs Anthropic CUA / OpenAI Operator

| 维度 | 闭源云端 CUA | cua-harness |
|---|---|---|
| 运行位置 | 云端虚拟桌面 | 用户本地 macOS |
| 数据 | 上传到云 | 完全本地 |
| 应用范围 | VM 内安装的 | 用户已有的全部 app |
| 成本 | API 计费 | 仅 LLM token |
| 模型自由度 | 绑定厂商 | 任何 LLM 都能驱动 |

定位差异：cua-harness 是**本地、open、模型无关**的 CUA 基础设施。

## 5. 用户旅程

**首次安装**：
1. `pip install cua-harness`
2. `cua-harness --doctor` → 提示安装 cua-driver / 授予 Accessibility 权限
3. 系统设置点 ✓，再跑一次 doctor → 全绿
4. `echo 'print(list_windows())' | cua-harness` 第一个 hello world

**日常使用**：
- agent 框架以 subprocess 起 `cua-harness`，stdin 喂代码，stdout 拿 JSON
- 不需要 SDK import，命名空间直接可用

**调试**：
- `cua-harness --reload` 重启守护进程
- `cua-harness --doctor` 自检
- `agent-workspace/agent_helpers.py` 手测各 helper

## 6. 成功指标

| 维度 | 指标 | 0.1.0 目标 |
|---|---|---|
| 可用性 | doctor 一次通过率 | ≥ 80% |
| 稳定性 | 24h 连续 1000 次 click 失败率 | < 1% |
| 性能 | `get_window_state(som)` p50 延迟 | < 500ms |
| 体积 | 安装大小（不含 cua-driver）| < 200KB |
| API 学习成本 | 22 helper 上手时间 | < 10min（看 SKILL.md）|

## 7. 发布计划

| 版本 | 内容 | 准入 |
|---|---|---|
| **0.1.0** | 当前功能 + 修 P0（JSON 静默、临时文件泄漏、stderr 吞）| pytest 通过、TCC 流程文档化 |
| **0.1.1** | 修 P1/P2（exec 异常栈、agent_helpers 容错、`app_info` 命名）| 内部 dogfood 1 周 |
| **0.2.0** | `wait_for`、多显示器、AX diff | 至少 1 个外部 agent 框架接入 |
| **0.3.0** | 录制/回放（macro mode）、性能 profiler | 视用户反馈 |

## 8. 文档矩阵

| 文件 | 受众 | 用途 |
|---|---|---|
| `README.md` | 所有人 | 30s 上手 |
| `install.md` | 新装用户 | TCC 授权、cua-driver 安装 |
| `SKILL.md` | LLM agent | 喂给模型的工具说明 |
| `docs/technical-design.md` | 贡献者 | 架构、IPC 契约、已知问题 |
| `docs/product-design.md`（本文）| 决策者 | 定位、路线图 |
| `.claude/implementation-notes.md` | 后续维护 | 设计决策日志 |

## 9. 风险

| 风险 | 影响 | 缓解 |
|---|---|---|
| macOS Accessibility API 变更 | 全部 helper 失效 | 跟随 cua-driver 上游 |
| TCC 授权复杂、用户放弃 | 装机率低 | doctor 输出操作指引 |
| cua-driver 维护停滞 | 项目停滞 | 当前为薄封装，可换底层 |
| LLM 误操作（破坏性点击）| 用户数据风险 | 文档明示责任、未来加 dry-run 模式 |

## 10. 不做的事

- 不做跨平台（Linux/Windows 用各自 driver）
- 不做"智能"层（重试、规划、记忆都交给上层 agent）
- 不做云端托管（保持本地、open）
- 不内置 LLM 调用（与模型解耦）
