#!/usr/bin/env python3
"""无容器的本地 PostgreSQL（用 pgserver 自带的二进制）。

    uv run python scripts/devdb.py start|stop|status

- 数据目录：backend/.pgdata
- 监听：127.0.0.1:5432（可用 DEVDB_PORT 覆盖）
- 首次启动会建库 `flarum` 和同名账号，密码 flarum，
  与 docker-compose.yml 里的配置一致，所以 backend/.env 不用改。
"""
import argparse
import os
import sys
from pathlib import Path

import pgserver

BASE = Path(__file__).resolve().parent.parent
PGDATA = Path(os.environ.get("DEVDB_PGDATA", BASE / ".pgdata"))
SOCKET = PGDATA / "run"
LOG = PGDATA / "postgres.log"
PORT = int(os.environ.get("DEVDB_PORT", "5432"))


def _init() -> None:
    if (PGDATA / "PG_VERSION").exists():
        return
    # initdb 要求目录为空，socket 目录必须等它跑完再建
    PGDATA.mkdir(parents=True, exist_ok=True)
    # 注意：pgserver 会自己加 -D <pgdata>，这里不能再传
    pgserver.initdb(["-U", "postgres", "--auth=trust", "-E", "UTF8"], pgdata=PGDATA)
    SOCKET.mkdir(parents=True, exist_ok=True)
    with open(PGDATA / "postgresql.conf", "a", encoding="utf-8") as fh:
        fh.write(
            "\n# devdb\n"
            "listen_addresses = '127.0.0.1'\n"
            f"port = {PORT}\n"
            f"unix_socket_directories = '{SOCKET}'\n"
        )


def _running() -> bool:
    try:
        pgserver.pg_ctl(["status"], pgdata=PGDATA)
        return True
    except Exception:
        return False


def _psql(sql: str) -> str:
    # pgserver 会给命令行自动补 -D，psql 不需要数据目录，改走 TCP
    return pgserver.psql(
        ["-h", "127.0.0.1", "-p", str(PORT), "-U", "postgres", "-d", "postgres", "-tAc", sql]
    )


def start() -> None:
    _init()
    if _running():
        print(f"devdb 已在运行（{PGDATA}）")
    else:
        pgserver.pg_ctl(["-l", str(LOG), "-w", "start"], pgdata=PGDATA)
        print(f"devdb 已启动：127.0.0.1:{PORT}，数据在 {PGDATA}")

    exists = _psql("SELECT 1 FROM pg_roles WHERE rolname='flarum'").strip()
    if not exists:
        _psql("CREATE ROLE flarum LOGIN PASSWORD 'flarum' CREATEDB")
        print("已创建账号 flarum/flarum")

    has_db = _psql("SELECT 1 FROM pg_database WHERE datname='flarum'").strip()
    if not has_db:
        _psql("CREATE DATABASE flarum OWNER flarum")
        print("已创建数据库 flarum")

    print("DATABASE_URL=postgresql+asyncpg://flarum:flarum@127.0.0.1:%d/flarum" % PORT)


def stop() -> None:
    if not (PGDATA / "PG_VERSION").exists():
        print("devdb 还没有初始化过")
        return
    if not _running():
        print("devdb 未在运行")
        return
    pgserver.pg_ctl(["-m", "fast", "-w", "stop"], pgdata=PGDATA)
    print("devdb 已停止")


def status() -> None:
    try:
        print(pgserver.pg_ctl(["status"], pgdata=PGDATA))
    except Exception:
        print("devdb 未在运行")
        sys.exit(1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="本地 PostgreSQL（无容器）")
    ap.add_argument("action", choices=["start", "stop", "status"])
    globals()[ap.parse_args().action]()
