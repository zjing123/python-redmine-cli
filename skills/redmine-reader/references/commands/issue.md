# Issue 命令参考

## 目录

- [issue get](#issue-get)
- [issue list](#issue-list)
- [issue fields](#issue-fields)
- [issue schema](#issue-schema)

---

## issue get

查看单个 issue 详情。

```bash
redmine-cli -p <profile> issue get 123
redmine-cli issue get https://redmine.example.com/issues/123
redmine-cli -p <profile> issue get 123 -i journals,attachments,relations
redmine-cli -p <profile> issue get 123 --fields id,subject,status,description,assigned_to
```

| 选项 | 说明 |
|------|------|
| `-i`, `--include` | 逗号分隔的关联数据：`children`、`attachments`、`relations`、`journals`、`watchers`、`changesets` |
| `--fields` | 逗号分隔的输出字段（如 `id,subject,status`），减少输出量 |

**`-i` 选项详解**：
- `journals` — 评论和变更历史（查看 issue 的讨论记录时必加）
- `attachments` — 附件列表
- `relations` — 关联的其他 issue
- `children` — 子任务列表
- `watchers` — 观察者列表
- `changesets` — 关联的代码变更集

可组合使用：`-i journals,attachments,relations`

**`--fields` 常用值**：
- 核心字段：`id,subject,status,description,assigned_to,priority,project`
- 时间相关：`created_on,updated_on,due_date,closed_on`
- 进度相关：`done_ratio,estimated_hours,spent_hours`
- 分类相关：`tracker,category,fixed_version`
- 自定义字段：`custom_fields`

---

## issue list

列出 issue，支持丰富的过滤和排序。

```bash
redmine-cli -p <profile> issue list                                    # 全部
redmine-cli -p <profile> issue list --assigned-to-me                   # 指派给我
redmine-cli -p <profile> issue list --assigned-to-me --status open     # 我的打开 issue
redmine-cli -p <profile> issue list --assigned-to-me --status "*"      # 我的全部（含已关闭）
redmine-cli -p <profile> issue list --project-id 1 --status open       # 某项目的
redmine-cli -p <profile> issue list --limit 10 --sort updated_on:desc  # 最近更新
redmine-cli issue list --assigned-to-me --all-profiles                 # 遍历所有实例
redmine-cli -p <profile> issue list --fields id,subject,status         # 精简输出
```

| 选项 | 说明 |
|------|------|
| `--project-id` | 按项目 ID 过滤 |
| `--status` | 按状态：`open`、`closed`、`*`（全部）或数字状态 ID |
| `--assigned-to-id` | 按指派人用户 ID |
| `--assigned-to-me` | 快捷方式：当前认证用户的 issue |
| `--tracker-id` | 按跟踪器 ID 过滤 |
| `--priority-id` | 按优先级 ID 过滤 |
| `--author-id` | 按作者用户 ID 过滤 |
| `--category-id` | 按分类 ID 过滤 |
| `--fixed-version-id` | 按目标版本 ID 过滤 |
| `--parent-id` | 按父 issue ID 过滤 |
| `--query-id` | 使用 Redmine 中保存的自定义查询 ID |
| `--sort` | 排序表达式，如 `updated_on:desc`、`priority:asc`、`created_on:desc` |
| `-l`, `--limit` | 最大结果数（默认 50，`--all` 取消限制） |
| `--all` | 获取全部结果（无限制） |
| `--offset` | 分页偏移量 |
| `-i`, `--include` | 逗号分隔的关联数据 |
| `--fields` | 逗号分隔的输出字段 |
| `--all-profiles` | 遍历所有配置的 profile 并合并结果 |

**排序表达式**：
- `updated_on:desc` — 按更新时间降序（最近更新的在前）
- `created_on:desc` — 按创建时间降序
- `priority:desc` — 按优先级降序（高优先级在前）
- `priority:asc` — 按优先级升序
- 可组合：`priority:desc,updated_on:desc`

**多实例查询**（`--all-profiles`）：
结果中每条记录带 `_profile` 和 `_source_url` 字段标识来源实例，还有 `per_profile` 汇总每个实例的计数。

---

## issue fields

查看 issue 资源的所有可用字段（无需连接 Redmine）。

```bash
redmine-cli issue fields
```

用于了解 issue 数据结构中有哪些字段可用。

---

## issue schema

查看 issue 的创建模板，含必填/可选/只读/ID 字段。

```bash
redmine-cli issue schema               # 离线模式（无需连接）
redmine-cli -p <profile> issue schema --live  # 从 Redmine 获取实时枚举值
```

| 选项 | 说明 |
|------|------|
| `--live` | 从 Redmine 获取实时枚举值（状态、优先级、跟踪器等 ID → 名称映射） |

`--live` 返回当前 Redmine 实例中实际可用的状态 ID 映射（如 `1: New, 2: In Progress, 3: Resolved, 5: Closed`）、优先级映射、跟踪器映射等，帮助理解 issue 数据中数字 ID 的含义。
