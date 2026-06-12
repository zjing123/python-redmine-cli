# Redmine CLI 配置指南

本文档包含 `redmine-cli` 的完整配置方法，包括多实例管理、环境变量和配置文件手动编辑。

## 目录

- [安全提醒](#安全提醒)
- [配置优先级](#配置优先级)
- [方式一：命令行配置（推荐）](#方式一命令行配置推荐)
- [方式二：环境变量](#方式二环境变量)
- [方式三：命令行参数](#方式三命令行参数)
- [方式四：手动编辑配置文件](#方式四手动编辑配置文件)
- [配置文件权限](#配置文件权限)
- [多实例管理](#多实例管理)
- [Profile 选择优先级](#profile-选择优先级)
- [资源引用方式](#资源引用方式)

---

## 安全提醒

配置涉及 API Key 和密码，请注意：

- **不要在对话中回显真实凭证**，始终用占位符（如 `<api_key>`）代替
- **优先使用 `config set` 写入配置文件**，避免凭证出现在 shell history 或进程列表中
- 环境变量中的凭证可被同 shell 会话的进程读取，也容易被 `ps` 等工具暴露
- 命令行直接传 `--api-key` 的方式最不安全，仅用于临时调试

---

## 配置优先级

命令行参数 > 环境变量 > 配置文件。

配置文件路径：`~/.config/redmine-cli/config.yaml`

---

## 方式一：命令行配置（推荐）

```bash
# API Key 认证
redmine-cli config set --url https://redmine.example.com/ --api-key <api_key>

# 用户名密码认证
redmine-cli config set --url https://redmine.example.com/ --username <user> --password <password>

# 指定 profile 名称
redmine-cli config set --url https://staging.test/ --api-key <api_key> -p staging
```

不带 `-p` 时自动从 URL 提取 profile 名（如 `https://redmine.example.com` → profile 名 `redmine`）。

`config set` 将凭证写入配置文件，不会持久化在 shell history 的参数中。

**更新已有配置**：
```bash
redmine-cli config update --url https://new.test/ -p staging
redmine-cli config update --api-key <api_key> -p staging
redmine-cli config update --username <user> --password <password> -p staging
```

**删除 profile**：
```bash
redmine-cli config unset -p staging
```

---

## 方式二：环境变量

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
echo 'export REDMINE_API_KEY="<api_key>"' >> ~/.bashrc
source ~/.bashrc
```

⚠️ **注意**：环境变量仅影响当前 shell 会话，且可能被 `ps`、`/proc/<pid>/environ` 或 shell 历史记录捕获。`~/.bashrc` 中的值以明文存储，需确保文件权限为 `600`。

---

## 方式三：命令行参数

直接在命令中传入连接参数（适用于临时调试）：

```bash
redmine-cli --url https://redmine.example.com/ --api-key <api_key> issue list
```

⚠️ **不推荐**：凭证会出现在 shell history 和进程列表中。

---

## 方式四：手动编辑配置文件

编辑 `~/.config/redmine-cli/config.yaml`：

```yaml
profiles:
  redmine:
    url: https://redmine.example.com/
    api_key: <api_key>

  staging:
    url: https://staging.redmine.example.com/
    api_key: <api_key>

  prod:
    url: https://redmine.example.com/
    username: <user>
    password: <password>
```

## 配置文件权限

确保配置文件仅当前用户可读：

```bash
chmod 600 ~/.config/redmine-cli/config.yaml
```

`config list` 和 `config get` 命令输出时会对密钥自动掩码，可安全查看配置状态。

---

## 多实例管理

当用户有多个 Redmine 实例时，通过 profile 管理：

```bash
# 添加两个实例
redmine-cli config set --url https://redmine1.example.com/ --api-key <api_key> -p redmine1
redmine-cli config set --url https://redmine2.example.com/ --api-key <api_key> -p redmine2

# 查看所有实例
redmine-cli config profiles

# 查询单个实例
redmine-cli -p redmine1 issue list --assigned-to-me --status open
redmine-cli -p redmine2 issue list --assigned-to-me --status open

# 一条命令遍历所有实例
redmine-cli issue list --assigned-to-me --all-profiles
```

`--all-profiles` 结果中每条记录带 `_profile` 和 `_source_url` 字段标识来源实例。

---

## Profile 选择优先级

1. `-p` / `REDMINE_PROFILE` 环境变量（显式指定 profile 名）
2. 命令参数中使用完整 URL（自动从 URL 匹配 profile）
3. `--url` / `REDMINE_URL` 环境变量（直接 URL 覆盖）

---

## 资源引用方式

issue ID、项目 ID 等资源引用支持两种方式：

- **整数 ID**（需 `-p` 指定 profile）：`redmine-cli -p prod issue get 123`
- **完整 URL**（自动匹配 profile）：`redmine-cli issue get https://prod.example.com/issues/123`
