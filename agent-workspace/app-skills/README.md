# App Skills

Harness 自动学习到的 app 操作技能（可执行 Python 代码）。

## 结构

```
app-skills/
  <bundle_id>/
    helpers.py    # 当前可调用函数
```

每个 `bundle_id` 目录对应一个 macOS 应用。

## 生命周期

1. `get_window_state(pid)` 返回该 app 的 `app_skills` 路径（若 `helpers.py` 存在）
2. Agent 直接 `import` 并调用其中的函数，跳过 LLM 推理
3. `save_app_skill(bundle_id, code, reason)` 写入新版本
