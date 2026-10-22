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
# 1. 数据库：docker → podman → 本地 pgserver 自动回退
make db
#    网络受限、拉不了镜像时，直接用本地二进制（无需 root、无需镜像）：
#    make devdb

# 2. 后端
cd backend && cp .env.example .env    # 至少改掉 JWT_SECRET
make -C .. install
make -C .. migrate
make -C .. import        # 站上已有新帖时会拒绝执行，需 --force 才清空
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
- 折叠：超过 480px 的代码块、超过 560px 的高图默认收起，点下方按钮展开
- 账号：登录、登出（立即吊销 access token）、refresh 轮换、CSRF 双提交
- 用户列表：`/users`，按用户名筛选，显示注册时间、发帖数、讨论数
- 用户主页：`/u/:id`，资料 + 讨论/回复两个标签页
- 通知：回复、引用、最佳回复会通知对方；`/notifications` 可全部标为已读，
  顶栏「通知」显示未读数（60 秒轮询）
- 顶栏：讨论 / 用户 / 通知三个入口；右侧「发帖」和用户菜单（个人主页、设置、退出登录）
- 设置：`/settings` 改昵称、自我介绍、头像（PNG/JPEG/GIF/WebP，≤2 MB，
  校验文件头而非只看扩展名）和密码；改密码会吊销其他设备的 refresh token，
  前端提示重新登录
- 发帖：`/new` 新建讨论（标题、板块、Markdown 正文）
- 回复：讨论底部编辑器，支持引用某层楼（自动生成 Markdown 引用块）
- 编辑：作者或管理员可改自己的帖子（迁移的旧帖只读，避免 XML↔Markdown 失真）
- 管理：置顶/锁定、改标签、设为最佳回复，都会写入 `discussion_events`
- 预览：`POST /api/v1/preview` 与正式发帖共用同一套渲染+清洗
- 附件：`POST /api/v1/uploads`（multipart），图片/PDF/文本/zip，单个 ≤10 MB；
  文件名重写为 `<uuid>-<原名>`，按日期分目录存在 `data/public/assets/files/`

## 访问控制与限流

- 讨论默认**不公开**：未登录访客只能看到 `is_public=true` 的讨论，管理员在讨论页
  「设为公开 / 转为私密」切换；列表、标签计数、站点统计都按访客身份过滤
- 搜索需要登录（`GET /search` 走 `CurrentUser`）
- 帖子附件：游客只能访问「公开讨论正文里引用过」的文件，其余返回 401；
  头像、字体等公共资源不受限
- 限流用 slowapi，默认 300 次/分钟，另有：
  - 登录 10 次/分钟（防爆破）
  - 搜索 30 次/分钟
  - 发帖 10 次/小时、回复 30 次/小时、编辑 60 次/小时
  - 上传 20 次/小时
  多 worker 部署时把 `app/core/ratelimit.py` 的存储换成 Redis

## 约定

- **认证**：access/refresh 两个 JWT 全放 `HttpOnly` cookie；所有写操作要求
  `X-CSRF-Token` 与 cookie 双提交匹配。
- **密码**：新密码用 Argon2id；Flarum 迁移来的 bcrypt 在登录成功后自动升级。
- **内容**：新帖存 Markdown，渲染后经 nh3 清洗入 `body_html`；迁移数据保留原
  s9e HTML，`is_legacy=true`。
- **事件**：改标题/改标签等操作存在 `discussion_events`，不混进 posts。
- **搜索**：`pg_trgm` + `ILIKE`，见 `migrations/versions/*` 里的 GIN 索引。
