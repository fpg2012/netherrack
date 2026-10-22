# flarum-web

论坛重写：**FastAPI + PostgreSQL + React(TS)**。接口只提供 JSON，前端是纯 SPA，
视觉与只读版 `/workspace/flarum-view` 保持一致。

```
backend/    FastAPI + SQLAlchemy 2.0(async) + Alembic
frontend/   Vite + React 18 + TypeScript + TanStack Query
data/       从 Flarum 导出的 dump 与附件（不进 git）
```

## 本地起服务

```bash
# 1. 数据库（需要 docker 权限；或自备 PostgreSQL 14+）
make db

# 2. 后端
cd backend && cp .env.example .env    # 至少改掉 JWT_SECRET
make -C .. install
make -C .. migrate
make -C .. import
make -C .. backend                    # http://127.0.0.1:8000/api/docs

# 3. 前端
make -C .. frontend                   # http://localhost:5173
```

首次建库时如果还没有迁移文件：

```bash
cd backend && uv run alembic revision --autogenerate -m "initial schema"
```

## 已实现（M1 + M2 写操作）

- 浏览：讨论列表 / 标签筛选 / 帖子时间线 / 搜索 / 附件与 KaTeX
- 账号：登录、登出、refresh 轮换、CSRF 双提交
- 发帖：`/new` 新建讨论（标题、板块、Markdown 正文）
- 回复：讨论底部编辑器，支持引用某层楼（自动生成 Markdown 引用块）
- 编辑：作者或管理员可改自己的帖子（迁移的旧帖只读，避免 XML↔Markdown 失真）
- 管理：置顶/锁定、改标签、设为最佳回复，都会写入 `discussion_events`
- 预览：`POST /api/v1/preview` 与正式发帖共用同一套渲染+清洗

## 约定

- **认证**：access/refresh 两个 JWT 全放 `HttpOnly` cookie；所有写操作要求
  `X-CSRF-Token` 与 cookie 双提交匹配。
- **密码**：新密码用 Argon2id；Flarum 迁移来的 bcrypt 在登录成功后自动升级。
- **内容**：新帖存 Markdown，渲染后经 nh3 清洗入 `body_html`；迁移数据保留原
  s9e HTML，`is_legacy=true`。
- **事件**：改标题/改标签等操作存在 `discussion_events`，不混进 posts。
- **搜索**：`pg_trgm` + `ILIKE`，见 `migrations/versions/*` 里的 GIN 索引。
