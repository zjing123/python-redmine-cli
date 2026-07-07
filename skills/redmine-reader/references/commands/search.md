# Search 命令参考

全文搜索 Redmine 资源。

```bash
redmine-cli -p <profile> search "关键词"
redmine-cli -p <profile> search "登录报错" -r issues
redmine-cli -p <profile> search "API" -r issues,documents
redmine-cli -p <profile> search "部署" -r issues,wiki_pages,news
```

| 选项 | 说明 |
|------|------|
| `-r`, `--resources` | 逗号分隔的资源类型：`issues`、`wiki_pages`、`news`、`documents`、`changesets` |

默认搜索所有类型。指定 `-r issues` 只搜索 issue。

## 按项目搜索（`--project` / `-P`）

加 `--project`（短选项 `-P`）可把搜索范围限定到单个项目内（走 Redmine 项目级端点 `/projects/{id}/search.json`）。接受项目 identifier（如 `redminex`）或数字 id（如 `42`）。

```bash
redmine-cli -p <profile> search "关键词" --project <identifier>
redmine-cli -p <profile> search "API" -P 42 -r issues
```

适用场景：已知某 issue 所属项目，想确认"该项目内还有没有其他 ticket 提到相同内容"。可先用 `redmine-cli -p <profile> issue get <id>` 查出项目的 id/identifier，再带 `--project` 搜索。

注意：Redmine 全文搜索为分词匹配，索引包含 issue 正文与评论，因此关键词出现在评论里也会被命中。
