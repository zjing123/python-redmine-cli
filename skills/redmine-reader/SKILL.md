---
name: redmine-reader
description: >
  使用 redmine-cli 命令行工具只读查询 Redmine issue（工单/任务）。当用户要求查看、搜索、列出、分析
  Redmine issue/ticket/工单/任务，或用户提供 Redmine issue URL（如 https://redmine.example.com/issues/123），
  或用户提到"我的任务""分配给我的 issue""某个 issue 的详情""issue 列表"等场景时使用此 skill。
  也适用于用户要求查看项目信息、搜索 Redmine 内容、查看 issue 评论/附件/关联关系。
  注意：此 skill 仅支持读取操作，不涉及创建、修改和删除。
---

# Redmine Issue 只读查询

使用 `redmine-cli` 命令行工具查询 Redmine issue 数据。所有输出为 JSON 格式。详细参数表见 [`references/commands/issue.md`](references/commands/issue.md)。

## 适用范围

此 skill **仅支持 issue 的读取操作**：
- ✅ 查看 issue 详情
- ✅ 列出 issue（含过滤、排序、分页）
- ✅ 搜索 issue
- ✅ 查看 issue 的评论、附件、关联关系
- ✅ 查看 issue 字段定义和 schema（理解数字 ID 含义）
- ❌ 不涉及创建、修改、删除 issue
- ✅ 在必要时查看项目信息，用于了解 issue 所属项目的上下文
- ❌ 不涉及创建、修改、删除 issue
- ❌ 不涉及 user / time-entry / wiki-page 等其他资源类型

---

## 安全规则

在整个操作过程中遵守以下规则：

- **不回显凭证**：不要在对话输出中打印真实的 API Key、密码或 token。示例中用 `<api_key>` 等占位符代替。
- **不记录凭证**：不要将包含凭证的命令写入日志、文件或对话记录。
- **错误脱敏**：`ok=false` 时，只向用户转述错误要点（如"连接被拒绝""认证失败"），不要原样暴露返回中的完整 URL、账号名、配置文件路径等敏感字段。
- **安装需确认**：安装软件前先询问用户是否允许执行远程脚本。

---

## 前置检查

**仅在首次使用或连接失败时**执行以下检查，不要每次查询都跑。

### 1. redmine-cli 是否已安装

```bash
redmine-cli --version
```

若提示 `command not found`，询问用户是否允许安装：

```bash
curl -LsSf https://raw.githubusercontent.com/zjing123/python-redmine-cli/main/install.sh | sh
```

**不要在用户未确认的情况下执行远程安装脚本。**

### 2. 是否已配置连接

```bash
redmine-cli config profiles
```

返回空列表 → 需要先配置（见下方「快速配置」）。

### 3. 验证连接

```bash
redmine-cli -p <profile> config test
```

成功返回认证用户信息。失败 → 检查配置是否正确，向用户简洁转述原因。

---

## 快速配置

当用户没有配置 Redmine 连接时，引导完成以下步骤：

1. 登录 Redmine Web → 「我的账号」→ 复制 API 访问密钥
2. 执行配置（**优先使用配置文件方式，避免凭证进入 shell history**）：

```bash
# 推荐方式：redmine-cli config set 会安全写入配置文件
redmine-cli config set --url https://<redmine-host>/ --api-key <api_key>
```

**凭证保护要点**：
- `config set` 会将凭证写入 `~/.config/redmine-cli/config.yaml`，不会暴露在 shell history 的参数列表中
- 不要将真实 API Key 粘贴到对话输出中
- 不带 `-p` 时自动从 URL 提取 profile 名
- 也可用用户名密码：`--username <user> --password <pass>`，同样注意不要在对话中回显

如需多实例、环境变量等高级配置，读取 [`references/configuration.md`](references/configuration.md)。

---

## 命令概览

以下为常用命令速查。需要构造具体命令时，按资源类型读取对应的命令参考文件（见底部 References 表）。

### Profile 选择

查询时需指定使用哪个 Redmine 实例。三种方式：
1. `-p <profile>` 参数（最常用）
2. 命令中直接用完整 URL（自动匹配 profile）
3. `REDMINE_PROFILE` 环境变量（注意：仅影响当前 shell 会话，且可能被进程列表或日志捕获）

### issue get — 查看 issue 详情

```bash
redmine-cli -p <profile> issue get 123
redmine-cli issue get https://redmine.example.com/issues/123       # URL 自动匹配 profile
redmine-cli -p <profile> issue get 123 -i journals,attachments     # 含评论和附件
redmine-cli -p <profile> issue get 123 --fields id,subject,status  # 精简输出
```

`-i` 可选值：`children`、`attachments`、`relations`、`journals`（评论/历史）、`watchers`、`changesets`

### issue list — 列出 issue

**默认查询策略**：列表查询默认加 `--limit 20 --fields id,subject,status,priority,assigned_to,updated_on`，避免返回过多数据。仅在用户明确要求更多字段或全量数据时调整。

```bash
# 标准查询（推荐默认值）
redmine-cli -p <profile> issue list --limit 20 --fields id,subject,status,priority,assigned_to,updated_on

# 带过滤
redmine-cli -p <profile> issue list --assigned-to-me --status open --limit 20 --fields id,subject,status,priority,assigned_to,updated_on
redmine-cli -p <profile> issue list --project-id 1 --status open --limit 20 --fields id,subject,status,priority,assigned_to,updated_on

# 用户明确要求排序或更多数据时调整
redmine-cli -p <profile> issue list --limit 50 --sort updated_on:desc --fields id,subject,status
redmine-cli issue list --assigned-to-me --all-profiles  # 遍历所有实例
```

常用过滤：`--status`（`open`/`closed`/`*`）、`--assigned-to-me`、`--project-id`、`--sort`、`--limit`、`--all-profiles`

### search — 全文搜索

```bash
redmine-cli -p <profile> search "关键词" -r issues
```

### issue schema — 理解数字 ID

issue 数据中状态、优先级等为数字 ID。获取映射：

```bash
redmine-cli -p <profile> issue schema --live
```

### project — 查看项目上下文

当需要了解 issue 所属项目的背景信息时：

```bash
redmine-cli -p <profile> project list --fields id,name,identifier
redmine-cli -p <profile> project get <id_or_identifier> --fields id,name,identifier,description
```

---

## 输出格式与错误处理

所有命令输出 JSON：

```json
{"ok": true, "data": {"id": 1, "subject": "Test"}}          // 单条
{"ok": true, "total_count": 150, "data": [...]}              // 列表
{"ok": false, "error": "错误描述", "error_type": "ErrorType"} // 错误
```

**成功时**：检查 `ok` → 从 `data` 取数据 → 列表用 `total_count` 分页 → 多实例用 `_profile`/`_source_url` 区分。

**失败时**（`ok=false`）：
1. 提取 `error` 和 `error_type` 字段
2. 向用户**简洁转述**错误原因，如"认证失败，请检查 API Key 配置"或"未找到该 issue"
3. **不要**原样输出错误信息中可能包含的完整 URL、配置路径或账号信息

---

## 工作流示例

**查看我的任务**：
```bash
redmine-cli -p <profile> issue list --assigned-to-me --status open --limit 20 --fields id,subject,status,priority,assigned_to,updated_on
redmine-cli -p <profile> issue get <id> -i journals
```

**搜索 issue**：
```bash
redmine-cli -p <profile> search "登录报错" -r issues
```

**查看指定项目的 issue**：
```bash
# 先了解项目信息
redmine-cli -p <profile> project list --fields id,name,identifier
redmine-cli -p <profile> project get <id> --fields id,name,identifier,description
# 再查该项目下的 issue
redmine-cli -p <profile> issue list --project-id <id> --status open --limit 20 --fields id,subject,status,priority,assigned_to,updated_on
```

---

## Token 优化

- 列表查询始终加 `--fields` 限制输出字段
- 仅在确实需要评论/附件等数据时才加 `-i`
- 需要理解数字 ID 含义时才调用 `schema --live`

---

## References

| 文件 | 何时读取 |
|------|----------|
| [`references/commands/issue.md`](references/commands/issue.md) | 需要构造 issue 命令、查看完整参数表和过滤选项时 |
| [`references/commands/search.md`](references/commands/search.md) | 需要构造搜索命令、查看资源类型选项时 |
| [`references/configuration.md`](references/configuration.md) | 需要帮助用户配置多实例、环境变量、配置文件权限等 |
