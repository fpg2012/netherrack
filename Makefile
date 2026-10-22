# 数据库优先用 docker，没有 docker daemon 就退回 podman（两者都免 root 配置）
DB_ENGINE := $(shell docker info >/dev/null 2>&1 && echo docker || (command -v podman-compose >/dev/null 2>&1 && echo podman || echo none))

.PHONY: db db-down db-logs backend frontend install migrate import test lint build

db:            ## 启动本地 PostgreSQL 并等待就绪
ifeq ($(DB_ENGINE),docker)
	docker compose up -d db
else ifeq ($(DB_ENGINE),podman)
	podman-compose up -d db
else
	$(error 没有可用的 docker daemon 或 podman，先启动其中之一的数据库)
endif
	@echo "等待 PostgreSQL 就绪…"
	@for i in $$(seq 1 60); do pg_isready -h 127.0.0.1 -p 5432 >/dev/null 2>&1 && break || sleep 1; done
	@pg_isready -h 127.0.0.1 -p 5432

db-down:
ifeq ($(DB_ENGINE),docker)
	docker compose down
else ifeq ($(DB_ENGINE),podman)
	podman-compose down
endif

db-logs:
ifeq ($(DB_ENGINE),docker)
	docker compose logs -f db
else ifeq ($(DB_ENGINE),podman)
	podman-compose logs -f db
endif

install:
	cd backend && uv sync
	cd frontend && npm install

migrate:
	cd backend && uv run alembic upgrade head

import:
	cd backend && uv run python -m app.importers.flarum

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
