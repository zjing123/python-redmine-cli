# Redmine CLI

基于 [python-redmine](https://github.com/maxtepkeev/python-redmine) 封装的命令行工具，专为 AI Agent 调用设计。所有输出均为 JSON 格式。

## 特性

- **JSON First** — 所有输出为 JSON，`ok` 字段标识成功/失败
- **零交互** — 无交互式提示，所有参数通过 flags 或 `--json` 传入
- **Agent 友好** — 统一响应格式，便于程序解析
- **动态资源路由** — 通过 `resource` 命令操作任意 Redmine 资源类型
- **多环境** — 支持 profile 切换多套 Redmine 环境

## 安装

### uv tool 安装（推荐）

```bash
uv tool install /path/to/redmine-cli
```

### pipx 安装

```bash
pipx install /path/to/redmine-cli
```

### 开发模式

```bash
cd redmine-cli
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
```

### 更新

```bash
uv tool install --force /path/to/redmine-cli
```

## 配置

三种种方式，优先级：命令行参数 > 环境变量 > 配置文件。

### 环境变量

```bash
export REDMINE_URL="https://redmine.example.com/"
export REDMINE_API_KEY="your_api_key_here"
```

写入 shell 配置持久化：

```bash
echo 'export REDMINE_URL="https://redmine.example.com/"' >> ~/.bashrc
echo 'export REDMINE_API_KEY="your_api_key_here"' >> ~/.bashrc
source ~/.bashrc
```

### 命令行参数

```bash
redmine-cli --url https://redmine.example.com/ --api-key xxx issue list
```

### 配置文件 `~/.redmine-cli.yaml`

```yaml
default:
  url: https://redmine.example.com/
  api_key: your_api_key
  version: "5.0.0"

profiles:
  staging:
    url: https://staging.redmine.example.com/
    api_key: staging_key

  prod:
    url: https://redmine.example.com/
    username: admin
    password: secret
```

使用非默认 profile：

```bash
redmine-cli -p staging issue list
```

## 使用方法

### 连接测试

```bash
redmine-cli config test    # 测试连接
redmine-cli config show    # 显示当前 URL
```

### Issue 操作

```bash
# 列表
redmine-cli issue list                                    # 全部 issue
redmine-cli issue list --assigned-to-me                   # 指派给我的
redmine-cli issue list --assigned-to-me --status-id open  # 我的打开 issue
redmine-cli issue list --assigned-to-me --status-id "*"   # 我的全部 issue（含已关闭）
redmine-cli issue list --project-id 1 --status-id open    # 某项目的打开 issue
redmine-cli issue list --limit 10 --sort updated_on:desc  # 最近更新的 10 条

# 详情
redmine-cli issue get 123
redmine-cli issue get 123 -i journals,attachments,relations  # 含评论/附件/关联

# 创建
redmine-cli issue create --project-id 1 --subject "Bug report"
redmine-cli issue create --project-id 1 --subject "新功能" --tracker-id 2 --assigned-to-id 5
redmine-cli issue create --json '{"project_id":1,"subject":"标题","description":"内容","custom_fields":[{"id":1,"value":"值"}]}'

# 更新
redmine-cli issue update 123 --status-id 3 --notes "已修复"
redmine-cli issue update 123 --assigned-to-id 5
redmine-cli issue update 123 --json '{"status_id":3,"notes":"通过 JSON 更新"}'

# 删除
redmine-cli issue delete 123

# 复制
redmine-cli issue copy 123 --project-id 2

# Watcher
redmine-cli issue add-watcher 123 --user-id 5
redmine-cli issue remove-watcher 123 --user-id 5
```

### 工时管理

```bash
# 列表
redmine-cli time-entry list                                    # 全部工时
redmine-cli time-entry list --user-id 1                        # 某人全部工时
redmine-cli time-entry list --user-id 1 --from 2026-04-01 --to 2026-04-30  # 月度
redmine-cli time-entry list --user-id 1 --from 2026-04-09 --to 2026-04-15  # 7天
redmine-cli time-entry list --user-id 1 --from 2026-04-15 --to 2026-04-15  # 某一天
redmine-cli time-entry list --issue-id 123                     # 某 issue 的工时

# 创建
redmine-cli time-entry create --json '{"issue_id":123,"hours":2.5,"activity_id":9,"comments":"开发"}'

# 更新
redmine-cli time-entry update 1 --json '{"hours":3,"comments":"修正"}'

# 删除
redmine-cli time-entry delete 1
```

### 项目操作

```bash
redmine-cli project list
redmine-cli project get 1
redmine-cli project get my-project-identifier
redmine-cli project create --name "新项目" --identifier "new-project"
redmine-cli project update 1 --name "新名称"
redmine-cli project delete 1
redmine-cli project close 1      # Redmine >= 5.0
redmine-cli project reopen 1     # Redmine >= 5.0
redmine-cli project archive 1    # Redmine >= 5.0
redmine-cli project unarchive 1  # Redmine >= 5.0
```

### 用户操作

```bash
redmine-cli user list
redmine-cli user get 5
redmine-cli user get current         # 当前登录用户
redmine-cli user create --login "newuser" --firstname "First" --lastname "Last" --mail "a@b.com" --password "pass123"
redmine-cli user update 5 --firstname "NewName"
redmine-cli user delete 5
```

### Wiki 操作

```bash
redmine-cli wiki-page list --project-id 1
redmine-cli wiki-page get "PageTitle" --project-id 1
redmine-cli wiki-page create "NewPage" --project-id 1 --text "Page content"
redmine-cli wiki-page update "PageTitle" --project-id 1 --text "Updated content"
redmine-cli wiki-page delete "PageTitle" --project-id 1
```

### 搜索

```bash
redmine-cli search "关键词"
redmine-cli search "登录报错" --resources issue
```

### 通用资源路由

通过 `resource` 命令操作任意已注册的 Redmine 资源，无需专用子命令。

```bash
# 查看所有可用资源类型
redmine-cli resource types

# 列表
redmine-cli resource list tracker
redmine-cli resource list issue_status
redmine-cli resource list custom_field
redmine-cli resource list role

# 获取单个
redmine-cli resource get tracker 1
redmine-cli resource get issue 123

# 过滤
redmine-cli resource filter issue --json '{"project_id":1,"status_id":"open"}'
redmine-cli resource filter time-entry --json '{"user_id":1,"from_date":"2026-04-01","to_date":"2026-04-30"}'
redmine-cli resource filter enumeration --json '{"resource":"time_entry_activities"}'
redmine-cli resource filter project_membership --json '{"project_id":1}'

# 创建
redmine-cli resource create issue --json '{"project_id":1,"subject":"标题"}'
redmine-cli resource create version --json '{"project_id":1,"name":"v1.0"}'

# 更新
redmine-cli resource update issue 123 --json '{"status_id":3,"notes":"已解决"}'

# 删除
redmine-cli resource delete issue 123
```

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

### 错误

```json
{"ok": false, "error": "Requested resource doesn't exist", "error_type": "ResourceNotFoundError"}
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
redmine-cli resource types                                    # 发现可用资源
redmine-cli issue list --assigned-to-me --status-id open      # 查看我的任务
redmine-cli issue get 123 -i journals                         # 查看详情+评论
redmine-cli issue update 123 --status-id 3 --notes "已修复"   # 更新状态
redmine-cli time-entry create --json '...'                    # 登记工时
```

Agent 解析逻辑：

1. `json.loads(stdout)` 解析输出
2. 检查 `ok` 字段判断成功/失败
3. 从 `data` 字段获取业务数据
4. 列表数据通过 `total_count` 实现分页

## 开发

```bash
cd redmine-cli
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# 运行测试
pytest tests/ -v

# 安装到全局（测试全局命令）
uv tool install --force .
```

## 项目结构

```
redmine-cli/
├── pyproject.toml
├── redmine_cli/
│   ├── __init__.py
│   ├── main.py              # Click 根入口
│   ├── context.py            # 延迟连接初始化
│   ├── config.py             # 配置管理
│   ├── output.py             # JSON 输出/错误处理
│   ├── utils.py              # 序列化工具
│   └── resources/
│       ├── issue.py          # Issue CRUD
│       ├── project.py        # Project CRUD
│       ├── user.py           # User CRUD
│       ├── time_entry.py     # TimeEntry CRUD
│       ├── wiki_page.py      # WikiPage CRUD
│       └── generic.py        # 动态资源路由
└── tests/cli/
    ├── conftest.py
    ├── test_output.py
    ├── test_config.py
    ├── test_utils.py
    ├── test_issue_cli.py
    └── test_generic_cli.py
```

## 依赖

- [python-redmine](https://github.com/maxtepkeev/python-redmine) >= 2.5.0
- [Click](https://click.palletsprojects.com/) >= 8.1.0
- [PyYAML](https://pyyaml.org/) >= 6.0

## License

Apache-2.0
