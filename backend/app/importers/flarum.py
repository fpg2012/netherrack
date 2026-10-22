"""把 Flarum 的 mysqldump 导入 PostgreSQL。

用法：
    cd backend
    python -m app.importers.flarum --dump ../data/flarum-2026-10-23.sql.gz

导入是「全量重建」：先清空目标表，再写入。只在初始化时运行。
"""
import argparse
import asyncio
import json
import sys
from datetime import UTC, datetime

from sqlalchemy import delete, func, select, text

from app.core.config import settings
from app.db.session import SessionLocal
from app.models import Discussion, DiscussionEvent, DiscussionTag, Post, Tag, Upload, User
from app.services.content import render_legacy_s9e
from app.services.dump import parse
from app.services.search import index_text, segment

TABLES = {
    "flarum_users", "flarum_tags", "flarum_discussions", "flarum_posts",
    "flarum_discussion_tag", "flarum_fof_upload_files",
    "flarum_groups", "flarum_group_user",
}

def _dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value).replace(tzinfo=UTC)


def _int(value: str | None, default: int | None = None) -> int | None:
    return int(value) if value not in (None, "") else default


SEQUENCES = {
    "users": "id", "tags": "id", "discussions": "id", "posts": "id",
    "discussion_events": "id", "uploads": "id", "refresh_tokens": "id",
}


async def _resync_sequences(session) -> None:
    """我们写入的是 Flarum 的显式主键，序列必须手动推到最大值之后。"""
    for table, column in SEQUENCES.items():
        await session.execute(text(
            f"SELECT setval(pg_get_serial_sequence('{table}', '{column}'), "
            f"COALESCE((SELECT MAX({column}) FROM {table}), 1))"
        ))
    await session.commit()


async def reset(session) -> None:
    # 顺序照顾外键：先删引用方
    for model in (DiscussionEvent, Post, DiscussionTag, Discussion, Tag, Upload, User):
        await session.execute(delete(model))
    await session.execute(text("ALTER SEQUENCE IF EXISTS posts_id_seq RESTART WITH 1"))
    await session.commit()


async def import_dump(path: str, force: bool = False) -> None:
    data = parse(path, TABLES)
    users = data["flarum_users"][1]
    cols = {name: idx for idx, name in enumerate(data["flarum_users"][0])}

    async with SessionLocal() as session:
        # 导入会清空数据库：只要存在「不是从 Flarum 迁移来的」帖子，就说明站上
        # 已经有真实内容，必须显式 --force 才允许覆盖
        existing = await session.scalar(
            select(func.count()).select_from(Post).where(Post.is_legacy.is_(False))
        ) or 0
        if existing and not force:
            print(
                f"拒绝导入：数据库里有 {existing} 条站内新建的帖子。\n"
                "如果确定要清空重建，请加 --force。",
                file=sys.stderr,
            )
            raise SystemExit(1)
        await reset(session)

        for row in users:
            session.add(User(
                id=_int(row[cols["id"]]),
                username=row[cols["username"]],
                email=row[cols["email"]] or f"user{row[cols['id']]}@example.invalid",
                password_hash=row[cols["password"]] or "",
                nickname=row[cols["nickname"]] or None,
                avatar_path=row[cols["avatar_url"]] or None,
                bio=row[cols["bio"]] or None,
                is_active=not bool(row[cols["suspended_until"]]),
                joined_at=_dt(row[cols["joined_at"]]) or datetime.now(UTC),
            ))
        await session.commit()

        # Flarum 的 Admin 组映射成 is_admin
        gcols = {n: i for i, n in enumerate(data["flarum_groups"][0])}
        admin_groups = {
            _int(row[gcols["id"]])
            for row in data["flarum_groups"][1]
            if (row[gcols["name_singular"]] or "").lower() in {"admin", "administrator"}
        }
        gu_cols = {n: i for i, n in enumerate(data["flarum_group_user"][0])}
        admin_users = [
            _int(row[gu_cols["user_id"]])
            for row in data["flarum_group_user"][1]
            if _int(row[gu_cols["group_id"]]) in admin_groups
        ]
        for user in await session.scalars(select(User)):
            user.is_admin = user.id in admin_users
        await session.commit()

        # 标签
        tcols = {n: i for i, n in enumerate(data["flarum_tags"][0])}
        tags = {}
        for row in data["flarum_tags"][1]:
            tag = Tag(
                id=_int(row[tcols["id"]]),
                name=row[tcols["name"]],
                slug=row[tcols["slug"]],
                color=row[tcols["color"]] or None,
                is_qna=row[tcols["is_qna"]] == "1",
                position=_int(row[tcols["position"]], 0),
            )
            tags[tag.id] = tag
            session.add(tag)
        await session.commit()

        # 上传记录（正文里的 /assets/files/... 靠它还原）
        ucols = {n: i for i, n in enumerate(data["flarum_fof_upload_files"][0])}
        uploads = {}
        for row in data["flarum_fof_upload_files"][1]:
            rec = Upload(
                uuid=row[ucols["uuid"]],
                path=row[ucols["path"]],
                filename=row[ucols["base_name"]],
                size=_int(row[ucols["size"]], 0),
                mime=row[ucols["type"]] or None,
                uploader_id=_int(row[ucols["actor_id"]]),
                created_at=_dt(row[ucols["created_at"]]) or datetime.now(UTC),
            )
            uploads[rec.uuid] = rec
            session.add(rec)
        await session.commit()

        # 讨论（隐藏的整条跳过，其下的帖子/标签也要一起跳过）
        dcols = {n: i for i, n in enumerate(data["flarum_discussions"][0])}
        keep: set[int] = set()
        for row in data["flarum_discussions"][1]:
            if row[dcols["hidden_at"]]:
                continue
            keep.add(_int(row[dcols["id"]]))
            session.add(Discussion(
                id=_int(row[dcols["id"]]),
                title=row[dcols["title"]],
                search_text=segment(row[dcols["title"]]),
                slug=row[dcols["slug"]] or None,
                author_id=_int(row[dcols["user_id"]]),
                is_sticky=row[dcols["is_sticky"]] == "1",
                is_locked=row[dcols["is_locked"]] == "1",
                created_at=_dt(row[dcols["created_at"]]) or datetime.now(UTC),
                last_posted_at=_dt(row[dcols["last_posted_at"]]),
            ))
        await session.commit()

        # 讨论-标签
        for row in data["flarum_discussion_tag"][1]:
            if _int(row[0]) not in keep:
                continue
            session.add(DiscussionTag(discussion_id=_int(row[0]), tag_id=_int(row[1])))
        await session.commit()

        # 帖子 / 操作记录
        pcols = {n: i for i, n in enumerate(data["flarum_posts"][0])}
        best: dict[int, int] = {}
        counts: dict[int, int] = {}
        for row in data["flarum_posts"][1]:
            pid = _int(row[pcols["id"]])
            did = _int(row[pcols["discussion_id"]])
            if did not in keep:
                continue
            kind = row[pcols["type"]] or "comment"
            created = _dt(row[pcols["created_at"]]) or datetime.now(UTC)

            if kind != "comment":
                try:
                    payload = json.loads(row[pcols["content"]] or "null")
                except ValueError:
                    payload = None
                session.add(DiscussionEvent(
                    id=pid, discussion_id=did, actor_id=_int(row[pcols["user_id"]]),
                    kind=kind, payload=payload, created_at=created,
                ))
                continue

            html = render_legacy_s9e(
                row[pcols["content"]] or "",
                {u: None for u in uploads},       # 只需要 uuid 存在性
            )
            session.add(Post(
                id=pid,
                discussion_id=did,
                number=_int(row[pcols["number"]], 1),
                author_id=_int(row[pcols["user_id"]]),
                body_html=html,
                search_text=index_text(html),
                is_legacy=True,
                created_at=created,
                edited_at=_dt(row[pcols["edited_at"]]),
                edited_by_id=_int(row[pcols["edited_user_id"]]),
                hidden_at=_dt(row[pcols["hidden_at"]]),
            ))
            counts[did] = counts.get(did, 0) + 1

        # 指向最佳回复的外键要在帖子写入之后补
        for row in data["flarum_discussions"][1]:
            did = _int(row[dcols["id"]])
            if did not in keep:
                continue
            ba = _int(row[dcols["best_answer_post_id"]])
            if ba:
                best[did] = ba
        await session.commit()

        for did, pid in best.items():
            discussion = await session.get(Discussion, did)
            if discussion:
                discussion.best_answer_post_id = pid
        for did, n in counts.items():
            discussion = await session.get(Discussion, did)
            if discussion:
                discussion.post_count = n
        await session.commit()

        await _resync_sequences(session)
        total = await session.scalar(select(func.count()).select_from(Post))
        print(f"导入完成：{len(users)} 用户 / {len(tags)} 标签 / "
              f"{len(data['flarum_discussions'][1])} 讨论 / {total} 帖子", file=sys.stderr)


def main() -> None:
    ap = argparse.ArgumentParser(description="导入 Flarum dump")
    ap.add_argument("--dump", default=str(settings.legacy_dump))
    ap.add_argument("--force", action="store_true", help="即使站内已有新帖也清空重建")
    args = ap.parse_args()
    asyncio.run(import_dump(args.dump, force=args.force))


if __name__ == "__main__":
    main()
