.PHONY: db backend frontend install migrate import test lint

db:            ## 启动本地 PostgreSQL（需要 docker 权限）
	docker compose up -d db

install:       ## 安装依赖
	cd backend && uv sync
	cd frontend && npm install

migrate:       ## 建表
	cd backend && uv run alembic upgrade head

import:        ## 导入 Flarum 数据
	cd backend && uv run python -m app.importers.flarum

backend:       ## http://127.0.0.1:8000
	cd backend && uv run uvicorn app.main:app --reload --port 8000

frontend:      ## http://127.0.0.1:5173
	cd frontend && npm run dev

test:
	cd backend && uv run pytest -q

lint:
	cd backend && uv run ruff check .
	cd frontend && npx tsc --noEmit

build:
	cd frontend && npm run build
