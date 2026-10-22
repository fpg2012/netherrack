# 数据库优先用 docker，没有 docker daemon 就退回 podman（两者都免 root 配置）
.PHONY: db db-down db-logs devdb devdb-stop backend frontend install migrate import import-force reindex test lint build

db:            ## 启动本地 PostgreSQL（docker → podman → pgserver 自动回退）
	./scripts/db.sh up

db-down:
	./scripts/db.sh down

db-logs:
	./scripts/db.sh logs

devdb:         ## 强制使用本地 pgserver（不碰容器）
	cd backend && uv run python scripts/devdb.py start

devdb-stop:
	cd backend && uv run python scripts/devdb.py stop

install:
	cd backend && uv sync
	cd frontend && npm install

migrate:
	cd backend && uv run alembic upgrade head

import:
	cd backend && uv run python -m app.importers.flarum

reindex:       ## 重建搜索分词（改分词方式后跑一次）
	cd backend && uv run python -m scripts.reindex_search

embeds:        ## 重新渲染旧帖里的 YouTube / Bilibili 嵌入
	cd backend && uv run python -m scripts.restore_embeds

mentions:      ## 清理迁移数据里的 @"name"#p123，改成可点击的 @name
	cd backend && uv run python -m scripts.fix_legacy_mentions

import-force:
	cd backend && uv run python -m app.importers.flarum --force

backend:
	cd backend && uv run uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

test:
	cd backend && uv run pytest -q

lint:
	cd backend && uv run ruff check .
	cd frontend && npx tsc --noEmit

build:
	cd frontend && npm run build
