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
