# 部署与配置

## 配置

配置分两层，优先级 **环境变量 > `.env` > `config.toml` > 代码默认值**：

| 文件 | 内容 |
|---|---|
| `backend/config.toml` | 非敏感项：站点名、env/debug、token 有效期、cookie 策略、CORS、分页、上传上限、路径 |
| `backend/.env` | 只放密钥：`DATABASE_URL`、`JWT_SECRET`，可选 `CONFIG_FILE` |

`backend/.env.example` 是模板。`JWT_SECRET` 没有默认值，缺失时后端拒绝启动：

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

常用配置项（`config.toml`）：

| 键 | 默认 | 说明 |
|---|---|---|
| `app_name` | `netherrack` | OpenAPI 标题 |
| `timezone` | `Asia/Shanghai` | 展示用时区（数据库统一存 UTC） |
| `default_tag` | 空 | 发帖时默认勾选的板块（标签 slug）；留空或标签不存在则不预选 |
| `env` | `dev` | `production` 时触发启动校验 |
| `debug` | `false` | `true` 才开放 `/api/docs` 和 `/api/openapi.json` |
| `access_token_ttl` | `900` | access token 有效期（秒） |
| `refresh_token_ttl` | `604800` | refresh token 有效期（秒） |
| `cookie_secure` | `false` | 走 HTTPS 时必须 `true` |
| `cors_origins` | `["http://localhost:5173"]` | 允许的前端来源 |
| `trust_proxy` | `false` | 反代后面设 `true`，限流按真实 IP 计数 |
| `upload_max_bytes` | `5242880` | 附件单文件上限（5 MB） |
| `avatar_max_bytes` | `2097152` | 头像上限（2 MB） |
| `assets_dir` | `../data/public/assets` | 附件根目录，相对 `backend/` 解析 |
| `legacy_dump` | `../data/flarum-*.sql.gz` | 迁移用 dump 路径 |

`CONFIG_FILE` 可指向代码目录外的 TOML，例如 `/etc/netherrack/config.toml`。
改完配置需要重启后端。

### 生产环境校验

`ENV=production` 时启动会检查，任一不满足直接失败：

- `cookie_secure` 必须为 `true`
- `cors_origins` 不能包含 localhost / 127.0.0.1
- `jwt_secret` 不能是默认值

## 部署

`deploy/nginx.conf.example` 是完整的反代示例，包含：

- HTML 的 CSP、HSTS、`X-Frame-Options` 等安全头（API 和 `/media` 的安全头由后端加）
- `/api/v1/stream` 的 SSE 长连接配置（关缓冲、放宽读超时）
- `X-Forwarded-For` + 后端 `TRUST_PROXY=true`，限流按真实 IP 计数

后端建议用 systemd 或 supervisor 托管，保持**单 worker**（原因见下）。

```ini
# /etc/systemd/system/netherrack.service
[Unit]
Description=netherrack
After=network.target postgresql.service

[Service]
WorkingDirectory=/srv/netherrack/backend
EnvironmentFile=/srv/netherrack/backend/.env
ExecStart=/srv/netherrack/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

数据库和附件需要定期备份：`pg_dump` + `data/public/assets` 打包，两者缺一不可
（帖子正文在库里，图片在磁盘上）。

### 多 worker 的坑

有两处状态在进程内存里，加 `--workers N` 会静默失效：

| 组件 | 表现 | 修法 |
|---|---|---|
| 限流 | 额度变成 N 倍，防爆破失效 | `Limiter(storage_uri="redis://…")` |
| SSE 事件总线 | 用户连在 A、通知产生在 B，收不到推送（退化为 2 分钟轮询） | Postgres `LISTEN/NOTIFY` 或 Redis pub/sub |

数据库、会话、通知已读状态、审计日志都在 PostgreSQL 里，多 worker 天然一致。
