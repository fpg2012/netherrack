<p align="center">
  <img src="docs/netherrack.svg" width="72" height="72" alt="netherrack">
</p>

<h1 align="center">netherrack</h1>

<p align="center">
  从 Flarum 迁移而来的轻量论坛 —— FastAPI + PostgreSQL + React
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-0.160-009688?style=flat-square&logo=fastapi&logoColor=white">
  <img alt="PostgreSQL" src="https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white">
  <img alt="React" src="https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black">
  <img alt="TypeScript" src="https://img.shields.io/badge/TypeScript-5-3178C6?style=flat-square&logo=typescript&logoColor=white">
</p>

## 简介

一个自己用的论坛，用来替换跑了五年的 Flarum。后端只输出 JSON，前端是纯 SPA，
界面刻意保持极简：单色、1px 边框、等宽小标签。

项目名 **netherrack**（地狱岩），站点本身的品牌名是 **soulsand**，
显示在顶栏和页面标题里。

已有的 152 个讨论、520 个帖子从 Flarum 完整迁移过来，包括标签、附件、
KaTeX 公式、@ 提及和 B 站 / YouTube 视频嵌入。

## 功能

**浏览**
- 讨论列表、标签筛选、分页；置顶只在标签内生效，避免霸占首页
- 帖子按楼层分页，操作记录（改名、置顶、锁帖）夹在时间线里显示
- 中文搜索：jieba 分词 + PostgreSQL 全文检索，`ts_headline` 摘要
- KaTeX 公式；旧帖里的 YouTube / Bilibili 播放器；超过一屏的代码块和高图自动折叠
- 附件支持图片 / 音视频 / PDF / 文本 / zip，上限可在配置里改

**写作**
- Markdown 编辑器，带预览、附件上传、`@` 自动补全（跟随光标、键盘可选）
- 引用某层楼，或直接「回复某一楼」通知作者
- 新帖和回复的草稿自动存 localStorage，刷新不丢
- 单独成段的 B 站 / YouTube 链接自动变成播放器

**账号与通知**
- 登录、登出（立即吊销 access token）、refresh 轮换、CSRF 双提交
- `/settings` 改昵称、自我介绍、头像、密码
- 通知：回复 / 引用 / 最佳回复 / @ 提及 / 系统通知；SSE 即时推送未读数
- 用户列表与个人主页（讨论 / 回复两个标签页）

**管理**
- 置顶、锁定、改标签、设为最佳回复
- 折叠整个讨论或单个楼层（折叠的讨论强制不公开、不进列表；折叠楼层显示占位）
- 设为公开 / 转为私密（管理员和楼主）
- 发送系统通知、审计日志

## 技术栈

| 层 | 选型 |
|---|---|
| 后端 | FastAPI · SQLAlchemy 2.0 (async) · Alembic · asyncpg |
| 数据库 | PostgreSQL 16（`tsvector` 生成列 + GIN 索引） |
| 前端 | Vite · React 18 · TypeScript · TanStack Query |
| 鉴权 | JWT（HttpOnly cookie）+ refresh 轮换 + CSRF 双提交 |
| 清洗 | nh3（标签/属性白名单）、KaTeX、markdown-it |
| 限流 | slowapi（默认按进程内存） |

## 快速开始

需要 Python 3.12+、Node 20+、PostgreSQL 14+（或已安装的 docker / podman）。

```bash
git clone git@github.com:fpg2012/netherrack.git
cd netherrack

# 1. 后端依赖与配置
cp backend/.env.example backend/.env
python3 -c "import secrets; print(secrets.token_hex(32))"   # 填进 .env 的 JWT_SECRET

make install

# 2. 数据库（docker → podman → 本地 pgserver 自动回退）
make db
make migrate

# 3. 起服务
make backend     # http://127.0.0.1:8000
make frontend    # http://localhost:5173
```

没有 docker 或拉不动镜像时，用 `make devdb` 起一个本地 PostgreSQL 16（无需 root）。

导入 Flarum 数据（需要把 dump 和附件放到 `data/` 下）：

```bash
make import      # 站上已有新帖时会拒绝执行，加 --force 才清空
make mentions    # 清理旧数据里的 @"name"#p123
make reindex     # 重建搜索分词
```

## 配置

配置分两层，优先级 **环境变量 > `.env` > `config.toml` > 代码默认值**：

| 文件 | 内容 |
|---|---|
| `backend/config.toml` | 非敏感项：站点名、env/debug、token 有效期、cookie 策略、CORS、分页、上传上限、路径 |
| `backend/.env` | 只放密钥：`DATABASE_URL`、`JWT_SECRET`，可选 `CONFIG_FILE` |

`ENV=production` 时后端会强制校验：`COOKIE_SECURE=true`、CORS 不含 localhost、
`JWT_SECRET` 不是默认值，任一不满足直接启动失败。

相对路径（`assets_dir`、`legacy_dump`）按 `backend/` 解析；改完配置需要重启后端。

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

## 部署

`deploy/nginx.conf.example` 是完整的反代示例，包含：

- HTML 的 CSP、HSTS、`X-Frame-Options` 等安全头（API 和 `/media` 由后端负责）
- `/api/v1/stream` 的 SSE 长连接配置（关缓冲、放宽读超时）
- `X-Forwarded-For` + 后端 `TRUST_PROXY=true`，限流按真实 IP 计数

后端建议用 systemd 或 supervisor 托管，保持**单 worker**（原因见下）。

### 多 worker 的坑

有两处状态在进程内存里，加 `--workers N` 会静默失效：

| 组件 | 表现 | 修法 |
|---|---|---|
| 限流 | 额度变成 N 倍，防爆破失效 | `Limiter(storage_uri="redis://…")` |
| SSE 事件总线 | 用户连在 A、通知产生在 B，收不到推送（退化为 2 分钟轮询） | Postgres `LISTEN/NOTIFY` 或 Redis pub/sub |

数据库、会话、通知已读状态、审计日志都在 PostgreSQL 里，多 worker 天然一致。

## 测试

```bash
make test     # cd backend && uv run pytest
```

集成测试用真实 PostgreSQL（复用 `DATABASE_URL`），每个用例包在外层事务里、
结束整体回滚，不会动开发库的数据，所以跑之前数据库要在运行。

## 已知限制

- 迁移过来的旧帖只读：Flarum 存的是 s9e XML，没有 Markdown 原文，编辑会覆盖排版
- 「私密」只是对游客隐藏，登录用户之间互相可见
- 新用户只能通过导入产生，没有注册、邮箱验证、找回密码
- 视频嵌入按域名白名单（YouTube / Bilibili），会在页面加载时请求第三方

## 许可证

仓库目前为私有，尚未附许可证。转为公开前需要选定（如 MIT 或 AGPL-3.0）。
