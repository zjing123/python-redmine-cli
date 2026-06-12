# Redmine CLI

基于 [python-redmine](https://github.com/maxtepkeev/python-redmine) 封装的命令行工具，专为 AI Agent 调用设计。所有输出均为 JSON 格式。

## 特性

- **JSON First** — 所有输出为 JSON，`ok` 字段标识成功/失败
- **零交互** — 无交互式提示，所有参数通过 flags、`--json` 或 `--stdin` 传入
- **Agent 友好** — 统一响应格式，便于程序解析
- **动态资源路由** — 通过 `resource` 命令操作任意 Redmine 资源类型
- **多实例管理** — 支持 profile 配置多套 Redmine 环境，`--all-profiles` 一键遍历
- **配置管理** — `config set/get/list` 命令行管理配置，密钥自动掩码
- **Dry-Run 模式** — `--dry-run` 预览 API 请求，不实际执行
- **Schema 发现** — `fields` / `schema` 子命令查看资源字段与创建模板

## 安装

### 一键安装（推荐）

```bash
# 从 GitHub 远程安装（自动安装 uv + redmine-cli）
curl -LsSf https://raw.githubusercontent.com/zjing123/python-redmine-cli/main/install.sh | sh

# 私有仓库用 SSH 协议
GIT_PROTO=ssh curl -LsSf https://raw.githubusercontent.com/zjing123/python-redmine-cli/main/install.sh | sh
```

已安装时重复运行会自动升级。

### 从 GitHub 直接安装

```bash
uv tool install git+https://github.com/zjing123/python-redmine-cli.git
```

### 本地安装

```bash
uv tool install /path/to/redmine-cli
```

### pipx 安装

```bash
pipx install /path/to/redmine-cli
```

### 开发模式

```bash
git clone https://github.com/zjing123/python-redmine-cli.git
cd python-redmine-cli
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
```

## 快速开始

```bash
# 1. 配置连接（使用 API Key）
#    不带 -p 时自动从 URL 提取 profile 名（如 https://redmine.example.com -> redmine）
redmine-cli config set --url https://redmine.example.com/ --api-key your_api_key_here

# 或使用用户名密码
redmine-cli config set --url https://redmine.example.com/ --username admin --password secret

# 2. 测试连接（需要指定 profile，或使用环境变量）
redmine-cli -p redmine config test

# 3. 开始使用（-p 指定 profile）
redmine-cli -p redmine issue list --assigned-to-me --status open

# 4. 也可以直接用完整 URL（自动匹配 profile）
redmine-cli issue get https://redmine.example.com/issues/123

# 5. 查看版本
redmine-cli --version
```

## 全局选项

以下选项可用于所有命令：

| 选项 | 短选项 | 环境变量 | 说明 |
|------|--------|----------|------|
| `--profile` | `-p` | `REDMINE_PROFILE` | 使用指定的连接 profile |
| `--url` | | `REDMINE_URL` | 本次调用覆盖 Redmine 服务器 URL |
| `--api-key` | | `REDMINE_API_KEY` | 本次调用覆盖 API Key |
| `--dry-run` | | | 预览将发送的 API 请求，不实际执行 |
| `--version` | | | 显示版本号 |

Profile 选择优先级：

1. `-p` / `REDMINE_PROFILE` 环境变量（显式指定 profile 名）
2. 命令参数中使用完整 URL（自动从 URL 匹配 profile）
3. `--url` / `REDMINE_URL` 环境变量（直接 URL 覆盖）

资源引用（`ISSUE_REF`、`PROJECT_REF` 等）支持：

- **整数 ID**（需要 `-p` 指定 profile）：`redmine-cli -p prod issue get 123`
- **完整 URL**（自动匹配 profile）：`redmine-cli issue get https://prod.example.com/issues/123`

## 配置

配置优先级：命令行参数 > 环境变量 > 配置文件。

配置文件路径：`~/.config/redmine-cli/config.yaml`

### 方式一：命令行配置（推荐）

```bash
# 使用 API Key
redmine-cli config set --url https://redmine.example.com/ --api-key your_api_key_here

# 使用用户名密码
redmine-cli config set --url https://redmine.example.com/ --username admin --password secret

# 指定 profile 名称
redmine-cli config set --url https://staging.test --api-key secret -p staging
```

### 方式二：环境变量

| 环境变量 | 说明 |
|----------|------|
| `REDMINE_URL` | Redmine 服务器 URL |
| `REDMINE_API_KEY` | API Key |
| `REDMINE_USERNAME` | 用户名 |
| `REDMINE_PASSWORD` | 密码 |
| `REDMINE_PROFILE` | Profile 名称 |
| `REDMINE_CONFIG` | 配置文件路径（覆盖默认路径） |
| `REDMINE_VERSION` | Redmine API 版本 |

写入 shell 配置持久化：

```bash
echo 'export REDMINE_URL="https://redmine.example.com/"' >> ~/.bashrc
echo 'export REDMINE_API_KEY="your_api_key_here"' >> ~/.bashrc
source ~/.bashrc
```

### 方式三：命令行参数

```bash
redmine-cli --url https://redmine.example.com/ --api-key xxx issue list
```

### 方式四：手动编辑配置文件

编辑 `~/.config/redmine-cli/config.yaml`：

```yaml
profiles:
  redmine:
    url: https://redmine.example.com/
    api_key: your_api_key

  staging:
    url: https://staging.redmine.example.com/
    api_key: staging_key

  prod:
    url: https://redmine.example.com/
    username: admin
    password: secret
```

使用指定 profile：

```bash
redmine-cli -p redmine issue list
```

## 命令参考

### config — 管理连接配置

管理存储在 `~/.config/redmine-cli/config.yaml` 的连接配置。

```bash
# 查看配置文件路径
redmine-cli config path

# 列出所有实例及其 URL（不暴露凭证）
redmine-cli config profiles

# 显示当前连接 URL
redmine-cli config show

# 测试连接，返回认证用户信息
redmine-cli config test

# 以 JSON 查看所有配置（密钥掩码）
redmine-cli config list

# 查看指定 profile 配置
redmine-cli config list --profile staging

# 以表格查看所有配置（供人工查看）
redmine-cli config list --print

# 创建 profile（自动从 URL 提取名称）
redmine-cli config set --url https://redmine.example.com/ --api-key xxx

# 使用用户名密码创建 profile
redmine-cli config set --url https://redmine.example.com/ --username admin --password secret

# 创建指定名称 profile
redmine-cli config set --url https://staging.test/ --api-key xxx -p staging

# 更新 profile 的 URL
redmine-cli config update --url https://new.test/ -p staging

# 更新 profile 的 API Key
redmine-cli config update --api-key newkey -p staging

# 切换为用户名密码认证
redmine-cli config update --username admin --password secret -p staging

# 查看某项值（密钥自动掩码）
redmine-cli config get url

# 查看指定 profile 的值
redmine-cli config get api_key -p staging

# 删除整个 profile
redmine-cli config unset -p staging
```

### 多实例配置

当有多个 Redmine 实例时，通过 profile 管理：

```bash
# 添加两个实例
redmine-cli config set --url https://redmine1.example.com/ --api-key key1 -p redmine1
redmine-cli config set --url https://redmine2.example.com/ --api-key key2 -p redmine2

# 查看所有实例
redmine-cli config list

# 查询单个实例
redmine-cli -p redmine1 issue list --assigned-to-me --status open
redmine-cli -p redmine2 issue list --assigned-to-me --status open

# 一条命令遍历所有实例（结果带 _profile 和 _source_url 字段区分来源）
redmine-cli issue list --assigned-to-me --all-profiles
```

### issue — Issue 操作

Issue CRUD、Watcher 管理、复制，支持过滤和多实例查询。

#### issue get

```bash
redmine-cli issue get 123
redmine-cli issue get 123 -i journals,attachments,relations  # 含评论/附件/关联
redmine-cli issue get 123 --fields id,subject,status         # 只输出指定字段
redmine-cli issue get https://redmine.example.com/issues/123  # URL 自动匹配 profile
```

| 选项 | 说明 |
|------|------|
| `-i`, `--include` | 逗号分隔的关联数据：`children`, `attachments`, `relations`, `journals`, `watchers`, `changesets` |
| `--fields` | 逗号分隔的输出字段（如 `id,subject,status`），减少输出量 |

#### issue list

```bash
redmine-cli issue list                                    # 全部 issue
redmine-cli issue list --assigned-to-me                   # 指派给我的
redmine-cli issue list --assigned-to-me --status open     # 我的打开 issue
redmine-cli issue list --assigned-to-me --status "*"      # 我的全部 issue（含已关闭）
redmine-cli issue list --project-id 1 --status open       # 某项目的打开 issue
redmine-cli issue list --limit 10 --sort updated_on:desc  # 最近更新的 10 条
redmine-cli issue list --assigned-to-me --all-profiles    # 遍历所有实例
redmine-cli issue list --fields id,subject,status         # 只输出指定字段
```

| 选项 | 说明 |
|------|------|
| `--project-id` | 按项目 ID 过滤 |
| `--status` | 按状态过滤：`open`, `closed`, `*`（全部）或数字状态 ID |
| `--assigned-to-id` | 按指派人用户 ID 过滤 |
| `--assigned-to-me` | 快捷方式：当前认证用户的 issue |
| `--all-profiles` | 查询所有配置的 profile 并合并结果（带 `_profile` 和 `_source_url` 字段） |
| `--tracker-id` | 按跟踪器 ID 过滤 |
| `--priority-id` | 按优先级 ID 过滤 |
| `--author-id` | 按作者用户 ID 过滤 |
| `--category-id` | 按分类 ID 过滤 |
| `--fixed-version-id` | 按目标版本 ID 过滤 |
| `--parent-id` | 按父 issue ID 过滤 |
| `--query-id` | 使用保存的查询 ID |
| `--sort` | 排序表达式，如 `updated_on:desc` 或 `priority:asc` |
| `-l`, `--limit` | 最大结果数（默认 50，用 `--all` 取消限制） |
| `--all` | 获取全部结果（无限制） |
| `--offset` | 分页偏移量 |
| `-i`, `--include` | 逗号分隔的关联数据 |
| `--fields` | 逗号分隔的输出字段 |

#### issue create

```bash
redmine-cli issue create --project-id 1 --subject "Bug report"
redmine-cli issue create --project-id 1 --subject "新功能" --tracker-id 2 --assigned-to-id 5
redmine-cli issue create --project-id 1 --subject "带自定义字段" --custom-fields '[{"id":1,"value":"值"}]'
redmine-cli issue create --project-id 1 --subject "带观察者" --watcher-user-ids 5,6,7
redmine-cli issue create --json '{"project_id":1,"subject":"标题","description":"内容"}'

# 通过 stdin 传入 JSON（避免 shell 转义问题，推荐 Agent 使用）
echo '{"project_id":1,"subject":"标题"}' | redmine-cli issue create --stdin
```

| 选项 | 说明 |
|------|------|
| `--json` | JSON 字符串包含所有字段 |
| `--stdin` | 从 stdin 读取 JSON |
| `--project-id` | 项目 ID（必填） |
| `--subject` | Issue 标题 |
| `--description` | Issue 描述 |
| `--tracker-id` | 跟踪器 ID |
| `--status-id` | 状态 ID |
| `--priority-id` | 优先级 ID |
| `--assigned-to-id` | 指派人用户 ID |
| `--parent-issue-id` | 父 issue ID |
| `--fixed-version-id` | 目标版本 ID |
| `--custom-fields` | 自定义字段 JSON 数组 |
| `--watcher-user-ids` | 逗号分隔的观察者用户 ID |

#### issue update

```bash
redmine-cli issue update 123 --status-id 3 --notes "已修复"
redmine-cli issue update 123 --assigned-to-id 5
redmine-cli issue update 123 --private-notes --notes "内部备注"
redmine-cli issue update 123 --json '{"status_id":3,"notes":"通过 JSON 更新"}'
echo '{"status_id":3}' | redmine-cli issue update 123 --stdin
```

| 选项 | 说明 |
|------|------|
| `--json` | JSON 字符串包含更新字段 |
| `--stdin` | 从 stdin 读取 JSON |
| `--subject` | 新标题 |
| `--description` | 新描述 |
| `--status-id` | 新状态 ID |
| `--assigned-to-id` | 新指派人用户 ID |
| `--priority-id` | 新优先级 ID |
| `--fixed-version-id` | 新目标版本 ID |
| `--notes` | 添加评论/备注 |
| `--private-notes` | 标记备注为私有 |
| `--custom-fields` | 自定义字段 JSON 数组 |

#### issue delete

```bash
redmine-cli issue delete 123
redmine-cli issue delete https://redmine.example.com/issues/123
```

#### issue add-watcher / remove-watcher

```bash
redmine-cli issue add-watcher 123 --user-id 5
redmine-cli issue remove-watcher 123 --user-id 5
```

| 选项 | 说明 |
|------|------|
| `--user-id` | 用户 ID（必填） |

#### issue copy

```bash
redmine-cli issue copy 123 --project-id 2                    # 复制到项目 2（默认链接原 issue）
redmine-cli issue copy 123 --project-id 2 --no-link-original # 复制但不链接原 issue
redmine-cli issue copy 123 --project-id 2 --include subtasks,attachments  # 含子任务和附件
```

| 选项 | 说明 |
|------|------|
| `--project-id` | 目标项目 ID |
| `--link-original` / `--no-link-original` | 是否链接到原 issue（默认链接） |
| `--include` | 逗号分隔：`subtasks`, `attachments` |

#### issue fields

查看 issue 资源的所有可用字段（无需连接）。

```bash
redmine-cli issue fields
```

#### issue schema

查看 issue 的创建模板，含必填/可选/只读/ID 字段。

```bash
redmine-cli issue schema                    # 离线模式
redmine-cli issue schema --live             # 从 Redmine 获取实时枚举值（跟踪器、状态、优先级等）
```

| 选项 | 说明 |
|------|------|
| `--live` | 从 Redmine 获取实时枚举值 |

---

### project — 项目操作

项目 CRUD 及生命周期管理（关闭、重开、归档、取消归档）。

#### project get

```bash
redmine-cli project get 1
redmine-cli project get my-project-identifier
redmine-cli project get https://redmine.example.com/projects/my-project
redmine-cli project get 1 --fields id,name,identifier
```

| 选项 | 说明 |
|------|------|
| `--fields` | 逗号分隔的输出字段 |

#### project list

```bash
redmine-cli project list
redmine-cli project list -i trackers,issue_categories
redmine-cli project list --fields id,name,identifier
```

| 选项 | 说明 |
|------|------|
| `-i`, `--include` | 逗号分隔的关联数据：`trackers`, `issue_categories`, `enabled_modules`, `time_entry_activities` |
| `--fields` | 逗号分隔的输出字段 |
| `-l`, `--limit` | 最大结果数（默认 50） |
| `--all` | 获取全部结果 |
| `--offset` | 分页偏移量 |

#### project create

```bash
redmine-cli project create --name "新项目" --identifier "new-project"
redmine-cli project create --name "子项目" --identifier "sub" --parent-id 1 --tracker-ids 1,2,3
redmine-cli project create --json '{"name":"Test","identifier":"test"}'
echo '{"name":"Test","identifier":"test"}' | redmine-cli project create --stdin
```

| 选项 | 说明 |
|------|------|
| `--json` | JSON 字符串包含所有字段 |
| `--stdin` | 从 stdin 读取 JSON |
| `--name` | 项目名称 |
| `--identifier` | 项目标识符 |
| `--description` | 项目描述 |
| `--is-public` | 是否公开 |
| `--inherit-members` | 是否继承成员 |
| `--parent-id` | 父项目 ID |
| `--tracker-ids` | 逗号分隔的跟踪器 ID |

#### project update

```bash
redmine-cli project update 1 --name "新名称"
redmine-cli project update my-project --description "新描述"
redmine-cli project update 1 --json '{"name":"New Name"}'
echo '{"name":"New Name"}' | redmine-cli project update my-project --stdin
```

| 选项 | 说明 |
|------|------|
| `--json` | JSON 字符串包含更新字段 |
| `--stdin` | 从 stdin 读取 JSON |
| `--name` | 新名称 |
| `--description` | 新描述 |
| `--is-public` | 是否公开 |
| `--parent-id` | 新父项目 ID |

#### project delete

```bash
redmine-cli project delete 1
redmine-cli project delete my-project
```

#### project close / reopen / archive / unarchive

```bash
redmine-cli project close 1       # 关闭项目（Redmine >= 5.0）
redmine-cli project reopen 1      # 重开项目（Redmine >= 5.0）
redmine-cli project archive 1     # 归档项目（Redmine >= 5.0）
redmine-cli project unarchive 1   # 取消归档（Redmine >= 5.0）
```

#### project fields

```bash
redmine-cli project fields
```

#### project schema

```bash
redmine-cli project schema               # 离线模式
redmine-cli project schema --live        # 从 Redmine 获取可用跟踪器列表
```

---

### user — 用户操作

用户 CRUD，支持 `current` 获取当前登录用户。

#### user get

```bash
redmine-cli user get 5
redmine-cli user get current                        # 当前登录用户
redmine-cli user get current -i memberships,groups  # 含成员关系和分组
redmine-cli user get 5 --fields id,login,firstname,lastname
```

| 选项 | 说明 |
|------|------|
| `-i`, `--include` | 逗号分隔的关联数据：`memberships`, `groups` |
| `--fields` | 逗号分隔的输出字段 |

#### user list

```bash
redmine-cli user list
redmine-cli user list --status 1 --limit 10       # 活跃用户
redmine-cli user list --name "john"                # 按登录名/姓名/邮箱搜索
redmine-cli user list --group-id 3                 # 按组过滤
```

| 选项 | 说明 |
|------|------|
| `--status` | 按状态过滤：`1`=活跃, `2`=已注册, `3`=已锁定 |
| `--name` | 按登录名/姓/名/邮箱过滤 |
| `--group-id` | 按组 ID 过滤 |
| `-l`, `--limit` | 最大结果数（默认 50） |
| `--all` | 获取全部结果 |
| `--offset` | 分页偏移量 |
| `--fields` | 逗号分隔的输出字段 |

#### user create

```bash
redmine-cli user create --login "newuser" --firstname "First" --lastname "Last" --mail "a@b.com" --password "pass123"
redmine-cli user create --login "auto" --firstname "Auto" --lastname "User" --mail "a@b.com" --generate-password --send-information
redmine-cli user create --json '{"login":"admin","firstname":"Admin","lastname":"User","mail":"admin@test.com","password":"pass"}'
echo '{"login":"admin",...}' | redmine-cli user create --stdin
```

| 选项 | 说明 |
|------|------|
| `--json` | JSON 字符串包含所有字段 |
| `--stdin` | 从 stdin 读取 JSON |
| `--login` | 登录名 |
| `--firstname` | 名 |
| `--lastname` | 姓 |
| `--mail` | 邮箱 |
| `--password` | 密码 |
| `--auth-source-id` | 认证源 ID |
| `--must-change-password` | 强制首次登录修改密码 |
| `--generate-password` | 自动生成随机密码 |
| `--send-information` | 发送账户信息邮件 |

#### user update

```bash
redmine-cli user update 5 --firstname "NewName"
redmine-cli user update 5 --must-change-password
redmine-cli user update 5 --json '{"firstname":"NewName"}'
echo '{"firstname":"NewName"}' | redmine-cli user update 5 --stdin
```

| 选项 | 说明 |
|------|------|
| `--json` | JSON 字符串包含更新字段 |
| `--stdin` | 从 stdin 读取 JSON |
| `--firstname` | 新名 |
| `--lastname` | 新姓 |
| `--mail` | 新邮箱 |
| `--password` | 新密码 |
| `--must-change-password` | 强制下次修改密码 |

#### user delete

```bash
redmine-cli user delete 5
```

#### user fields

```bash
redmine-cli user fields
```

#### user schema

```bash
redmine-cli user schema
```

---

### time-entry — 工时管理

工时条目 CRUD，支持日期范围和项目/Issue 过滤。

#### time-entry get

```bash
redmine-cli time-entry get 123
redmine-cli time-entry get 123 --fields id,hours,spent_on,activity,comments
```

| 选项 | 说明 |
|------|------|
| `--fields` | 逗号分隔的输出字段 |

#### time-entry list

```bash
redmine-cli time-entry list                                    # 全部工时
redmine-cli time-entry list --user-id 1                        # 某人全部工时
redmine-cli time-entry list --user-id 1 --from 2026-04-01 --to 2026-04-30  # 月度
redmine-cli time-entry list --user-id 1 --from 2026-04-09 --to 2026-04-15  # 7天
redmine-cli time-entry list --user-id 1 --from 2026-04-15 --to 2026-04-15  # 某一天
redmine-cli time-entry list --issue-id 123                     # 某 issue 的工时
```

| 选项 | 说明 |
|------|------|
| `--project-id` | 按项目 ID 过滤 |
| `--issue-id` | 按 Issue ID 过滤 |
| `--user-id` | 按用户 ID 过滤 |
| `--activity-id` | 按活动类型 ID 过滤 |
| `--from` | 开始日期（YYYY-MM-DD） |
| `--to` | 结束日期（YYYY-MM-DD） |
| `-l`, `--limit` | 最大结果数（默认 50） |
| `--all` | 获取全部结果 |
| `--offset` | 分页偏移量 |
| `--fields` | 逗号分隔的输出字段 |

#### time-entry create

```bash
redmine-cli time-entry create --issue-id 123 --hours 2.5 --activity-id 1
redmine-cli time-entry create --json '{"issue_id":123,"hours":2.5,"activity_id":9,"comments":"开发"}'
echo '{"issue_id":123,"hours":2.5}' | redmine-cli time-entry create --stdin
```

| 选项 | 说明 |
|------|------|
| `--json` | JSON 字符串包含所有字段 |
| `--stdin` | 从 stdin 读取 JSON |
| `--issue-id` | Issue ID |
| `--project-id` | 项目 ID（与 `--issue-id` 二选一） |
| `--spent-on` | 日期（YYYY-MM-DD），默认今天 |
| `--hours` | 工时数 |
| `--activity-id` | 活动类型 ID |
| `--comments` | 备注 |

#### time-entry update

```bash
redmine-cli time-entry update 1 --hours 3.0
redmine-cli time-entry update 1 --json '{"hours":3,"comments":"修正"}'
echo '{"hours":3}' | redmine-cli time-entry update 1 --stdin
```

| 选项 | 说明 |
|------|------|
| `--json` | JSON 字符串包含更新字段 |
| `--stdin` | 从 stdin 读取 JSON |
| `--hours` | 新工时数 |
| `--activity-id` | 新活动类型 ID |
| `--comments` | 新备注 |
| `--spent-on` | 新日期（YYYY-MM-DD） |

#### time-entry delete

```bash
redmine-cli time-entry delete 1
```

#### time-entry fields

```bash
redmine-cli time-entry fields
```

#### time-entry schema

```bash
redmine-cli time-entry schema               # 离线模式
redmine-cli time-entry schema --live        # 从 Redmine 获取活动类型枚举
```

---

### wiki-page — Wiki 操作

Wiki 页面 CRUD（所有命令需要 `--project-id`）。

#### wiki-page get

```bash
redmine-cli wiki-page get "PageTitle" --project-id 1
redmine-cli wiki-page get "PageTitle" --project-id 1 --fields title,text,version
```

| 选项 | 说明 |
|------|------|
| `--project-id` | 项目 ID（必填） |
| `--fields` | 逗号分隔的输出字段 |

#### wiki-page list

```bash
redmine-cli wiki-page list --project-id 1
redmine-cli wiki-page list --project-id 1 --fields title,updated_on
```

| 选项 | 说明 |
|------|------|
| `--project-id` | 项目 ID（必填） |
| `-l`, `--limit` | 最大结果数（默认 50） |
| `--all` | 获取全部结果 |
| `--offset` | 分页偏移量 |
| `--fields` | 逗号分隔的输出字段 |

#### wiki-page create

```bash
redmine-cli wiki-page create "NewPage" --project-id 1 --text "Page content"
redmine-cli wiki-page create "NewPage" --project-id 1 --text "Content" --comments "Initial version"
redmine-cli wiki-page create "NewPage" --project-id 1 --json '{"text":"Content","comments":"Initial"}'
echo '{"text":"Content"}' | redmine-cli wiki-page create "NewPage" --project-id 1 --stdin
```

| 选项 | 说明 |
|------|------|
| `--project-id` | 项目 ID（必填） |
| `--json` | JSON 字符串包含所有字段 |
| `--stdin` | 从 stdin 读取 JSON |
| `--text` | 页面内容（textile 或 markdown，取决于 Redmine 配置） |
| `--comments` | 编辑备注 |

#### wiki-page update

```bash
redmine-cli wiki-page update "PageTitle" --project-id 1 --text "Updated content"
redmine-cli wiki-page update "PageTitle" --project-id 1 --text "New" --comments "Updated"
redmine-cli wiki-page update "PageTitle" --project-id 1 --json '{"text":"New content"}'
echo '{"text":"New content"}' | redmine-cli wiki-page update "PageTitle" --project-id 1 --stdin
```

| 选项 | 说明 |
|------|------|
| `--project-id` | 项目 ID（必填） |
| `--json` | JSON 字符串包含更新字段 |
| `--stdin` | 从 stdin 读取 JSON |
| `--text` | 新页面内容 |
| `--comments` | 编辑备注 |

#### wiki-page delete

```bash
redmine-cli wiki-page delete "PageTitle" --project-id 1
```

| 选项 | 说明 |
|------|------|
| `--project-id` | 项目 ID（必填） |

#### wiki-page fields

```bash
redmine-cli wiki-page fields
```

#### wiki-page schema

```bash
redmine-cli wiki-page schema
```

---

### search — 全文搜索

全文搜索 Redmine 资源（Issue、Wiki、新闻、文档、变更集等）。

```bash
redmine-cli search "关键词"
redmine-cli search "登录报错" -r issues
redmine-cli search "API" -r issues,documents
redmine-cli search "部署" -r issues,wiki_pages,news
```

| 选项 | 说明 |
|------|------|
| `-r`, `--resources` | 逗号分隔的资源类型（如 `issues`, `wiki_pages`, `news`, `documents`, `changesets`） |

---

### resource — 通用资源路由

通过 `resource` 命令操作任意已注册的 Redmine 资源，无需专用子命令。使用 `resource types` 查看所有可用资源类型。

#### resource types

```bash
redmine-cli resource types
```

#### resource get

```bash
redmine-cli resource get issue 123
redmine-cli resource get project my-project
redmine-cli resource get tracker 1
redmine-cli resource get issue 123 --fields id,subject,status
```

| 选项 | 说明 |
|------|------|
| `--fields` | 逗号分隔的输出字段 |

#### resource list

```bash
redmine-cli resource list tracker
redmine-cli resource list issue_status
redmine-cli resource list custom_field
redmine-cli resource list role
redmine-cli resource list enumeration
```

| 选项 | 说明 |
|------|------|
| `-l`, `--limit` | 最大结果数（默认 50） |
| `--all` | 获取全部结果 |
| `--offset` | 分页偏移量 |
| `--fields` | 逗号分隔的输出字段 |

#### resource filter

```bash
redmine-cli resource filter issue --json '{"project_id":1,"status_id":"open"}'
redmine-cli resource filter time-entry --json '{"user_id":1,"from_date":"2026-04-01","to_date":"2026-04-30"}'
redmine-cli resource filter enumeration --json '{"resource":"time_entry_activities"}'
redmine-cli resource filter project_membership --json '{"project_id":1}'
echo '{"project_id":1}' | redmine-cli resource filter issue --stdin
```

| 选项 | 说明 |
|------|------|
| `--json` | JSON 对象作为过滤条件 |
| `--stdin` | 从 stdin 读取 JSON |
| `-l`, `--limit` | 最大结果数（默认 50） |
| `--all` | 获取全部结果 |
| `--offset` | 分页偏移量 |
| `--fields` | 逗号分隔的输出字段 |

#### resource create

```bash
redmine-cli resource create issue --json '{"project_id":1,"subject":"标题"}'
redmine-cli resource create version --json '{"project_id":1,"name":"v1.0"}'
echo '{"project_id":1,"subject":"标题"}' | redmine-cli resource create issue --stdin
```

| 选项 | 说明 |
|------|------|
| `--json` | JSON 对象包含创建字段 |
| `--stdin` | 从 stdin 读取 JSON |

#### resource update

```bash
redmine-cli resource update issue 123 --json '{"status_id":3,"notes":"已解决"}'
redmine-cli resource update project test --json '{"name":"New Name"}'
echo '{"status_id":3}' | redmine-cli resource update issue 123 --stdin
```

| 选项 | 说明 |
|------|------|
| `--json` | JSON 对象包含更新字段 |
| `--stdin` | 从 stdin 读取 JSON |

#### resource delete

```bash
redmine-cli resource delete issue 123
redmine-cli resource delete version 5
```

#### resource fields

查看任意资源类型的可用字段（无需连接）。

```bash
redmine-cli resource fields issue
redmine-cli resource fields project
redmine-cli resource fields wiki_page
redmine-cli resource fields tracker
```

#### resource schema

查看任意资源类型的创建模板。

```bash
redmine-cli resource schema issue
redmine-cli resource schema project
redmine-cli resource schema wiki_page
redmine-cli resource schema issue --live   # 从 Redmine 获取实时枚举值
```

| 选项 | 说明 |
|------|------|
| `--live` | 从 Redmine 获取实时枚举值（跟踪器、状态、优先级等） |

## 输出格式

所有输出为 JSON，结构统一。

### 成功 — 单条

```json
{"ok": true, "data": {"id": 1, "subject": "Test"}}
```

### 成功 — 列表

```json
{"ok": true, "total_count": 150, "limit": 25, "offset": 0, "data": [...]}
```

### 成功 — 变更操作

```json
{"ok": true, "updated": true, "resource": "issue", "id": 123}
{"ok": true, "deleted": true, "resource": "issue", "id": 123}
```

### Dry-Run 输出

```bash
redmine-cli --dry-run issue create --project-id 1 --subject "Test"
```

```json
{"ok": true, "dry_run": true, "resource": "issue", "action": "create", "url": "https://redmine.example.com", "payload": {"project_id": 1, "subject": "Test"}}
```

### 错误

```json
{"ok": false, "error": "Requested resource doesn't exist", "error_type": "ResourceNotFoundError"}
```

### 多实例结果

使用 `--all-profiles` 时，每条记录带 `_profile` 和 `_source_url` 字段标识来源：

```json
{
  "ok": true,
  "total_count": 6,
  "data": [
    {"id": 1, "subject": "...", "_profile": "redmine1", "_source_url": "https://redmine1.example.com"},
    {"id": 5, "subject": "...", "_profile": "redmine2", "_source_url": "https://redmine2.example.com"}
  ],
  "per_profile": {
    "redmine1": {"url": "https://redmine1.example.com", "count": 3},
    "redmine2": {"url": "https://redmine2.example.com", "count": 3}
  }
}
```

### 退出码

| 退出码 | 含义 |
|--------|------|
| 0 | 成功 |
| 1 | 业务错误（认证失败、资源不存在等） |
| 2 | 参数错误 |

## Agent 集成

```bash
# 典型 Agent 工作流
redmine-cli config test                                        # 验证连接
redmine-cli resource types                                     # 发现可用资源
redmine-cli issue schema --live                                # 查看 issue 创建模板（含枚举值）
redmine-cli issue list --assigned-to-me --status open          # 查看我的任务
redmine-cli issue list --assigned-to-me --all-profiles         # 遍历所有实例
redmine-cli issue get 123 -i journals                          # 查看详情+评论
redmine-cli issue update 123 --status-id 3 --notes "已修复"    # 更新状态
redmine-cli time-entry create --json '...'                     # 登记工时
echo '...' | redmine-cli issue create --stdin                  # 通过 stdin 传入 JSON（推荐 Agent 使用）

# Dry-run 预览（Agent 安全网）
redmine-cli --dry-run issue update 123 --status-id 5           # 先预览，再执行
redmine-cli --dry-run issue delete 123                         # 预览删除操作

# 字段精简（减少 token 开销）
redmine-cli issue list --fields id,subject,status --limit 50
redmine-cli issue get 123 --fields id,subject,description,status,assigned_to
```

Agent 解析逻辑：

1. `json.loads(stdout)` 解析输出
2. 检查 `ok` 字段判断成功/失败
3. 从 `data` 字段获取业务数据
4. 列表数据通过 `total_count` 实现分页
5. 多实例数据通过 `_profile` / `_source_url` 区分来源
6. 变更操作检查 `updated` / `deleted` 字段确认结果

## 开发

```bash
git clone https://github.com/zjing123/python-redmine-cli.git
cd python-redmine-cli
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# 运行测试
pytest tests/ -v

# 安装到全局（测试全局命令）
uv tool install --force .
```

## 项目结构

```
python-redmine-cli/
├── pyproject.toml
├── README.md
├── install.sh                  # 一键安装脚本
├── src/cli/
│   ├── __init__.py
│   ├── main.py                 # Click 根入口 + 全局选项
│   ├── context.py              # 延迟连接初始化 + URL 自动匹配 profile
│   ├── config.py               # 配置管理（文件/环境变量/profiles）
│   ├── output.py               # JSON 输出 + 统一错误处理
│   ├── utils.py                # 序列化工具 + stdin/JSON 解析
│   ├── fields.py               # 资源字段元数据发现
│   ├── schema.py               # 资源创建模板 + 实时枚举值
│   ├── commands/               # 全局命令
│   │   ├── config.py           # config 子命令组（set/get/list/update/unset/test/path/profiles/show）
│   │   └── search.py           # 全文搜索
│   └── resources/              # 资源专用命令
│       ├── _shared.py          # 共享工具（dry-run、分页、字段过滤）
│       ├── issue.py            # Issue CRUD + watcher + copy + --all-profiles
│       ├── project.py          # Project CRUD + 生命周期（close/reopen/archive/unarchive）
│       ├── user.py             # User CRUD + current 用户
│       ├── time_entry.py       # TimeEntry CRUD
│       ├── wiki_page.py        # WikiPage CRUD
│       └── generic.py          # 动态资源路由（resource 命令）
└── tests/cli/
    ├── conftest.py
    ├── test_output.py
    ├── test_config.py
    ├── test_utils.py
    ├── test_issue_cli.py
    ├── test_stdin.py
    └── test_generic_cli.py
```

## 依赖

- [python-redmine](https://github.com/maxtepkeev/python-redmine) >= 2.5.0
- [Click](https://click.palletsprojects.com/) >= 8.1.0
- [PyYAML](https://pyyaml.org/) >= 6.0

## License

Apache-2.0
