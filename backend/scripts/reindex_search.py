#!/usr/bin/env python3
"""重建帖子搜索文本（分词结果）。

改了分词方式、或从旧版本升级后跑一次：
    uv run python -m scripts.reindex_search
"""
import asyncio

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Discussion, Post
from app.services.search import index_text, segment


async def main() -> None:
    async with SessionLocal() as session:
        posts = (await session.scalars(select(Post))).all()
        for post in posts:
            post.search_text = index_text(post.body_html)

        discussions = (await session.scalars(select(Discussion))).all()
        for discussion in discussions:
            discussion.search_text = segment(discussion.title)

        await session.commit()
        print(f"已重建 {len(posts)} 条帖子、{len(discussions)} 个讨论标题的搜索文本")


if __name__ == "__main__":
    asyncio.run(main())
