# 开发说明

## 目录结构

```
backend/
  app/
    api/routes/      # discussions / posts / users / notifications / stream / uploads …
    models/          # SQLAlchemy 模型
    services/        # s9e 解析、内容清洗、搜索、提及、通知、审计、SSE 事件总线
    core/            # 配置、鉴权、限流、安全响应头
    importers/       # Flarum 导入
  config.toml        # 非敏感配置
  migrations/        # Alembic
  scripts/           # devdb、重建分词、修复旧提及、恢复嵌入
  tests/             # 单元测试 + API 集成测试
frontend/
  src/
    pages/           # 首页 / 讨论 / 搜索 / 用户 / 通知 / 设置
    components/      # 编辑器、楼层、下拉、Toast、折叠 …
    api/             # 请求封装与 TanStack Query hooks
    lib/             # 草稿、KaTeX、格式化
deploy/
  nginx.conf.example # 反代 + 安全头 + SSE 配置
data/                # Flarum dump 与附件（不进 git）
```

## 开发

```bash
make install     # 后端 uv sync + 前端 npm install
make db          # 或 make devdb（无 docker 时用本地 pgserver）
make migrate
make backend     # uvicorn --reload
make frontend    # vite
```

常用命令：

| 命令 | 作用 |
|---|---|
| `make lint` | ruff + tsc |
| `make test` | pytest |
| `make build` | 前端生产构建 |
| `make reindex` | 重建搜索分词（改分词方式后跑一次） |
| `make mentions` | 清理旧数据里的 `@"name"#p123` |
| `make embeds` | 重新渲染旧帖里的视频嵌入 |
| `make import` | 从 `data/` 里的 dump 导入（`import-force` 会清库） |

## 测试

```bash
make test     # cd backend && uv run pytest
```

集成测试用真实 PostgreSQL（复用 `DATABASE_URL`），每个用例包在外层事务里、
结束整体回滚，不会动开发库的数据，所以跑之前数据库要在运行。

新增数据库字段时记得生成迁移：

```bash
cd backend && uv run alembic revision --autogenerate -m "change"
uv run alembic upgrade head
```

## 设计取舍与已知限制

- 迁移过来的旧帖只读：Flarum 存的是 s9e XML，没有 Markdown 原文，编辑会覆盖排版
- 「私密」只是对游客隐藏，登录用户之间互相可见
- 新用户只能通过导入产生，没有注册、邮箱验证、找回密码
- 视频嵌入按域名白名单（YouTube / Bilibili），会在页面加载时请求第三方
- 硬删除不做级联清理：删帖是软删（`hidden_at`），折叠只影响展示

## 许可证

项目采用 GPL-3.0-or-later 发布，详见 [LICENSE](LICENSE)。提交代码即表示同意按同一许可证发布。
