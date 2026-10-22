#!/usr/bin/env bash
# 启动本地 PostgreSQL：优先 docker，其次 podman，都不可用（或镜像拉不下来）
# 就退回 pgserver 的本地二进制。用法：scripts/db.sh up|down|logs
set -uo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"

container_up() {
  if docker info >/dev/null 2>&1; then
    (cd "$root" && docker compose up -d db) && return 0
  fi
  if command -v podman-compose >/dev/null 2>&1; then
    (cd "$root" && podman-compose up -d db) && return 0
  fi
  return 1
}

devdb() { (cd "$root/backend" && uv run python scripts/devdb.py "$1"); }

case "${1:-up}" in
  up)
    if container_up; then
      echo "使用容器里的 PostgreSQL"
    else
      echo "容器不可用或镜像拉取失败，改用本地 pgserver"
      devdb start
    fi
    for _ in $(seq 1 60); do
      pg_isready -h 127.0.0.1 -p 5432 >/dev/null 2>&1 && break
      sleep 1
    done
    pg_isready -h 127.0.0.1 -p 5432
    ;;
  down)
    if docker info >/dev/null 2>&1; then (cd "$root" && docker compose down)
    elif command -v podman-compose >/dev/null 2>&1; then (cd "$root" && podman-compose down)
    else devdb stop; fi
    ;;
  logs)
    if docker info >/dev/null 2>&1; then (cd "$root" && docker compose logs -f db)
    elif command -v podman-compose >/dev/null 2>&1; then (cd "$root" && podman-compose logs -f db)
    else tail -f "$root/backend/.pgdata/postgres.log"; fi
    ;;
  *) echo "用法: $0 up|down|logs" >&2; exit 2 ;;
esac
