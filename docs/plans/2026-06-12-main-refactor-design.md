# main.py 重构设计：commands 拆分与资源层共享助手

> 日期：2026-06-12
> 状态：已确认，待实施
> 关联：推翻 `docs/IMPROVEMENT_PLAN.md`「明确不做的」清单中两项

## 1. 背景与决策

`redmine_cli/main.py` 当前 475 行，承载三类职责：

- `cli` 根命令组 + 4 个全局选项（profile / url / api-key / dry-run）
- `config` 组及 9 个子命令（path/profiles/show/test/list/set/update/get/unset，占 ~350 行）
- `search` 命令（~44 行）
- 资源子命令注册

资源层（`resources/{issue,project,generic,time_entry,user,wiki_page}.py`）存在 5 类重复代码，共 20+ 处。

`docs/IMPROVEMENT_PLAN.md` 曾将「main.py 拆分」与「消除分页/重复」列入「明确不做的」清单。**2026-06-12 经重新评估决定推翻该判定并执行本次重构**，理由：

1. 资源层重复已达 20+ 处（分页 5、dry-run 16、fields 8、json fallback 4），新增资源命令时复制成本与出错面持续增长；
2. `commands/` 包拆分使 config/search 与资源命令组结构一致，降低定位与维护成本；
3. `tests/cli/` 已有 10 个测试文件覆盖关键路径，重构有回归兜底，风险可控。

## 2. 目标

- `main.py` 瘦身至 ~60 行（仅根命令 + 全局选项 + 子命令注册）。
- 5 类重复统一收敛到 `resources/_shared.py`。
- **零行为变更**：所有命令的 help、选项、输出 JSON 结构、退出码、dry-run 行为完全不变。
- 全量 `tests/cli/` 通过。

## 3. 不在范围内（YAGNI）

- 不改任何命令行为、help 文本、输出格式。
- 不移动 `resources/` 下已有命令组（issue/project 等仍留在 `resources/`）。
- 不新增单元测试；沿用现有 CliRunner 端到端测试。
- 不引入 worktree（单分支、纯重构、有测试兜底）。

## 4. 设计一：`resources/_shared.py`（第一步）

### 5 个共享助手

```python
from ..context import DRY_RUN_METHODS, build_dry_run_url
from ..output import emit, emit_dry_run
from ..utils import build_fields, resolve_json_data, resourceset_to_list


def slice_resourceset(rs, limit, fetch_all, offset):
    """Pure slicing. Returns (sliced_rs, original_total_count). No IO."""


def emit_resourceset(rs, *, limit, fetch_all, offset, fields=None, extra=None):
    """Slice + serialize + emit. Covers list / filter / project_list."""


def emit_dry_run_mutation(ctx, base_url, resource_type, operation, payload=None, **url_kw):
    """If dry-run active, emit would-be mutation and return True; else False."""


def resolve_fields(json_data, stdin_mode, **cli_kwargs):
    """--json/--stdin wins; else build from non-None CLI kwargs."""


def parse_fields(fields):
    """Comma-separated --fields -> list, or None."""
```

### 设计要点

- **分页拆两层**：`slice_resourceset`（纯切片，`_issue_list_all_profiles` 循环内累加 total 也复用）+ `emit_resourceset`（list/filter/project_list 一键调用）。
- **dry-run 返回 bool**：调用方 `if emit_dry_run_mutation(...): return`，从 4 行 → 2 行。
- 依赖 `utils` / `context` / `output`，**无循环导入**。

### Before / After（issue delete，dry-run 16 处之一）

```python
# before
if ctx.obj.get("_dry_run"):
    url = build_dry_run_url(rm.url, "issue", "delete", id=issue_id)
    emit_dry_run("delete", "issue", DRY_RUN_METHODS["delete"], url)
    return
rm.issue.delete(issue_id)

# after
if emit_dry_run_mutation(ctx, rm.url, "issue", "delete", id=issue_id):
    return
rm.issue.delete(issue_id)
```

### 影响面（第一步）

| 助手 | 调用点 |
|------|--------|
| `emit_resourceset` / `slice_resourceset` | issue.list、issue._all_profiles、generic.list、generic.filter、project.list |
| `emit_dry_run_mutation` | issue×6、generic×3、project×7、time_entry、user、wiki_page 全部 mutation |
| `parse_fields` | 所有 get/list 的 `fields.split(",")` |
| `resolve_fields` | issue/project/time_entry/user 的 create/update |

## 5. 设计二：`commands/` 拆分（第二步）

### 新增包结构

```
redmine_cli/
  main.py            # 瘦身至 ~60 行: cli 组 + 全局选项 + 注册
  config.py          # 配置读写模块 (不变)
  resources/         # 资源命令组 (不变 + _shared.py)
  commands/          # 新增
    __init__.py      # 聚合导出 config_group, search
    config.py        # config 组 + 9 子命令 (原样搬迁)
    search.py        # search 命令 (原样搬迁)
```

### 依赖

- `commands/config.py` ← `click`、`..config`（读写模块）、`..context.get_redmine`、`..output.{emit,handle_errors}`。命令组变量名 `config_group`，与读写模块 `redmine_cli/config.py` 仅包路径不同，**不冲突**。
- `commands/search.py` ← `click`、`..context.get_redmine`、`..output.{emit,handle_errors}`、`..utils.resourceset_to_list`。resourceset 判定逻辑特殊，**不套 `_shared`**，原样搬迁。

### main.py 瘦身后

```python
from .commands import config_group, search
from .resources import generic, issue, project, time_entry, user, wiki_page

# cli 组 + 4 全局选项 + ctx.ensure_object (保留原 41-65 行)

cli.add_command(config_group, "config")
cli.add_command(search)
cli.add_command(issue.issue_group, "issue")
# ... project / user / time-entry / wiki-page / resource 不变
```

### 不变项

- 入口 `redmine-cli = "redmine_cli.main:cli"`（pyproject）不变。
- config/search 行为、help、`--print` 表格逻辑原样搬迁，零变更。
- `tests/cli/test_config.py` 等经 `CliRunner` 调 `cli`，注册路径不变。

## 6. 实施顺序

1. **第一步**：创建 `resources/_shared.py` → 改造 6 个资源文件调用点 → 跑 `tests/cli/`。
2. **第二步**：建 `commands/` 包，搬迁 config/search → 瘦身 main.py → 跑 `tests/cli/`。
3. 全量回归 + 提交。

## 7. 风险与回退

- 风险点：dry-run URL 构造、分页切片边界、config 表格输出——均被现有测试覆盖。
- 回退：两步各自独立提交，任一步测试失败可单独 revert。
