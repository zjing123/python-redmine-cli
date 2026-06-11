# Redmine CLI 项目进度总结

## Goal

基于第三方库 [python-redmine](https://github.com/maxtepkeev/python-redmine) 创建一个独立的 CLI 工具 `redmine-cli`，供 AI Agent 通过 shell 调用操作 Redmine 项目管理系统。所有输出为 JSON 格式，便于程序解析。

## Instructions

- CLI 作为独立项目，不修改 python-redmine 库本身，仅作为依赖调用
- 所有命令输出统一 JSON 格式：`{"ok": true/false, "data": ..., "error": ...}`
- 零交互设计，所有参数通过 flags 或 `--json` 传入
- 支持多 Redmine 实例管理（profile 机制）
- 配置文件路径：`~/.config/redmine-cli/config.yaml`
- 提供 `config set/get/list/unset/profiles/path` 命令管理配置
- 密钥在 get/list 输出时自动掩码
- `--assigned-to-me` 快捷获取当前用户指派的 issue
- `--all-profiles` 一条命令遍历所有 Redmine 实例
- 退出码：0=成功，1=业务错误，2=参数错误
- 测试环境：`http://redminetest.kettle.net.cn:7777/redmine2/`，API Key: `f54822488ec92b67f32be1ce5af6f57be969e5f3`，用户名: `redmine`（admin）
- GitHub 仓库：`git@github.com:zjing123/python-redmine-cli.git`

## Discoveries

1. python-redmine 库架构清晰：`Redmine` 入口 → `ResourceManager` → `BaseResource`，资源通过 `registry` 自动注册，覆盖 20+ 种 Redmine 资源
2. Click 框架中 `--help` 也会触发 group callback，需要延迟初始化连接（lazy init via `context.py` 的 `get_redmine()`）
3. `main.py` 与 `resources/*.py` 之间会产生循环导入，解决方案是将 `get_redmine()` 放在独立的 `context.py` 中
4. Redmine search API 返回的 ResourceSet 需要手动序列化为 list，否则 JSON 输出会是对象字符串
5. Redmine API 的 `assigned_to_id` 支持 `me` 关键字，但 CLI 中用 `--assigned-to-me` 通过 `rm.auth().id` 获取更可靠
6. `uv tool install --force --reinstall` 可解决 uv 缓存不更新的问题
7. 配置文件中的 `api_key` 字段需要自动映射为 `key`（python-redmine 构造参数名）
8. 测试中 monkeypatch 删除环境变量时，如果不设置 `REDMINE_CONFIG` 指向临时路径，测试可能读到真实配置文件

## Accomplished

### 已完成

- ✅ 分析 python-redmine 库，确认可以封装为 CLI
- ✅ 编写详细构建文档 `docs/CLI_BUILD_PLAN.md`（在 python-redmine 仓库中）
- ✅ 创建独立项目 `redmine-cli`，完整实现所有功能模块
- ✅ 核心模块：config.py / output.py / utils.py / context.py / main.py
- ✅ 资源命令：issue.py / project.py / user.py / time_entry.py / wiki_page.py / generic.py
- ✅ 配置管理命令：config set/get/list/unset/profiles/path/test/show
- ✅ `--assigned-to-me` 快捷标志
- ✅ `--all-profiles` 多实例遍历查询
- ✅ 配置文件路径改为 `~/.config/redmine-cli/config.yaml`
- ✅ 22+ 个单元测试全部通过
- ✅ 真实 Redmine 环境端到端测试通过（config test / issue CRUD / time-entry / project / user / wiki-page / search / generic resource / delete）
- ✅ 全局安装验证通过（`uv tool install`，安装到 `/home/liuchuan/.local/bin/redmine-cli`）
- ✅ README.md 完整文档
- ✅ .gitignore 文件
- ✅ 推送到 GitHub：`git@github.com:zjing123/python-redmine-cli.git`

### 未来可做

- `time-entry list` 也添加 `--assigned-to-me` 和 `--all-profiles` 支持
- 更多资源类型的专用命令（version / news / issue_category 等）
- `--output=text/csv/table` 多种输出格式
- ✅ stdin 管道模式（`echo '{}' | redmine-cli issue create --stdin`）
- 批量操作命令
- Schema 发现命令（`redmine-cli resource schema issue`）
- MCP/Skill 集成封装
- CI/CD（GitHub Actions）

## Relevant files / directories

```
/home/liuchuan/Documents/liuchuan/redmine-cli/                    # 项目根目录
├── .gitignore
├── README.md                                                      # 完整使用文档
├── pyproject.toml                                                 # 项目配置，依赖 python-redmine>=2.5.0, click>=8.1.0, pyyaml>=6.0
├── redmine_cli/
│   ├── __init__.py
│   ├── main.py                                                    # Click 根入口 + config/search 命令
│   ├── context.py                                                 # get_redmine() 延迟连接初始化
│   ├── config.py                                                  # 配置管理（文件/环境变量/profiles），路径 ~/.config/redmine-cli/config.yaml
│   ├── output.py                                                  # JSON emit() + handle_errors 装饰器 + 错误码映射
│   ├── utils.py                                                   # 序列化工具（serialize/resourceset_to_list/parse_json_input/build_fields/resolve_json_data）
│   └── resources/
│       ├── __init__.py
│       ├── issue.py                                               # Issue CRUD + --assigned-to-me + --all-profiles
│       ├── project.py                                             # Project CRUD + close/reopen/archive/unarchive
│       ├── user.py                                                # User CRUD + "current" 支持
│       ├── time_entry.py                                          # TimeEntry CRUD + 日期范围过滤
│       ├── wiki_page.py                                           # WikiPage CRUD（需 --project-id）
│       └── generic.py                                             # 动态资源路由 + types 命令，利用 registry 自动发现
└── tests/
    ├── __init__.py
    └── cli/
        ├── __init__.py
        ├── conftest.py                                            # fixtures: runner, mock_redmine, set_env
        ├── test_output.py
        ├── test_config.py
        ├── test_utils.py
        ├── test_issue_cli.py
        ├── test_stdin.py
        └── test_generic_cli.py

/home/liuchuan/Documents/liuchuan/python-redmine/                  # 第三方依赖库（不修改）
└── docs/CLI_BUILD_PLAN.md                                         # 早期构建规划文档
```
