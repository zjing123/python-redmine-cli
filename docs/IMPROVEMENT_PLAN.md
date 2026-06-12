# redmine-cli 改进计划

> 定位：个人使用的 Agent 友好型 Redmine CLI 工具。以下分析基于此前提，排除不适用于个人项目的考量。

---

## P0 — Agent 直接报错或解析失败

### 1. `config list` 默认输出表格而非 JSON

**位置：** `redmine_cli/main.py:178-207`

README 声明"所有输出均为 JSON"，但 `config list` 不加 `--json` 时打印 ASCII 表格，Agent 解析会直接失败。`config list --json` 和 `config profiles` 返回结构也不一致（数组 vs 对象），Agent 在不同命令间切换需要处理不同结构。

### 2. 响应中资源 ID 字段名不统一

**位置：** 各 resource 文件

```
issue update       → {"updated": true, "issue_id": 123}
project update     → {"updated": true, "project_id": 123}
time-entry update  → {"updated": true, "time_entry_id": 123}
user update        → {"updated": true, "user_id": 123}
```

Agent 每次都要判断"这次返回的 ID 字段叫什么"，额外消耗 token。建议统一为：

```json
{"updated": true, "resource": "issue", "id": 123}
```

### 3. `add-watcher` / `remove-watcher` 响应双重嵌套 `ok`

**位置：** `redmine_cli/resources/issue.py:369,382`

`emit()` 已经包裹了 `{"ok": true, "data": ...}`，内部又手动构造了 `{"ok": true, ...}`，导致：

```json
{"ok": true, "data": {"ok": true, "issue_id": 123, "watcher_added": 5}}
```

Agent 解析时会困惑。

---

## P1 — Agent 效率大幅提升

### 4. `--fields` 扩展到所有 `get` 命令

**位置：** 所有 resource 文件

当前仅 `list`/`filter` 支持 `--fields`，`get` 永远返回完整对象（含 journals、attachments、custom fields），轻松几千 tokens。Agent 通常只需要 `id,subject,status,assigned_to` 几个字段。加上后单次查询从 ~3000 tokens 降到 ~200 tokens。

### 5. 无 `--dry-run` 模式

Agent 在执行 create/update/delete 前无法验证参数是否正确。dry-run 返回"将发送什么参数到哪个 endpoint"，避免"执行→报错→重试"的低效循环。

### 6. 无 Schema 发现命令

Agent 不知道创建资源需要哪些必填字段、有哪些可选值。`redmine-cli resource schema issue` 应返回 required/optional 字段列表及枚举值，让 Agent 一次做对。

### 7. ~~无 stdin 管道模式~~ ✅ 已完成

所有 mutation 命令已支持 `--stdin` 标志，与 `--json` 互斥。用法：`echo '...' | redmine-cli issue create --stdin`

---

## P2 — 顺手修

### 8. HTTP 无超时

**位置：** `redmine_cli/config.py:119`

`Redmine()` 未传 timeout，requests 默认无限等待。Agent 调用卡住不返回时排查困难。加 30s 默认超时即可。

### 9. `--limit 0` 语义不清

**位置：** 5 个 resource 文件

`0` 是合法限制值（返回 0 条），用它表示"无限制"让 Agent 困惑。改为 `None` 作默认值，`if limit is not None` 判断。

### 10. `json.loads` 错误信息不友好

**位置：** `redmine_cli/utils.py:31-33`

Agent 看到 `JSONDecodeError at line 1 column 15` 不知道是哪个参数出错，加上参数名前缀即可。

---

## 明确不做的

以下在通用项目审查中会被提出，但对个人 Agent 工具不值得花时间：

- 单元测试补齐（手动端到端验证足够）
- Shell 自动补全（给 Agent 用的，不是人敲的）
- `--all-profiles` 并行化（个人 1-2 个 profile，串行不是瓶颈）
- README 英文化、CHANGELOG、pyproject metadata
- 配置文件权限加固（个人机器）
- 真实 Redmine 集成测试

> **2026-06-12 更新：** 以下两项原列于本「不做」清单，经重新评估已决定执行，详见 [`docs/plans/2026-06-12-main-refactor-design.md`](plans/2026-06-12-main-refactor-design.md)：
>
> - `main.py` 拆分（拆出 `commands/config.py`、`commands/search.py`，main.py 瘦身至 ~60 行）
> - 消除分页/字段解析/dry-run 等资源层重复（抽取 `resources/_shared.py`）
