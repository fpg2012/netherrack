"""重新渲染带视频嵌入的旧帖（历史上 iframe 被清洗掉了）。

从原始 mysqldump 里取回 s9e XML，按当前的清洗规则重新生成 body_html。
可重复执行：只处理正文里存在空 <div class="embed"> 的帖子。
"""
import asyncio

from sqlalchemy import select

from app.core.config import settings
from app.db.session import SessionLocal
from app.models import Post, Upload
from app.services import dump
from app.services.content import render_legacy_s9e
from app.services.mentions import link_mentions, username_map
from app.services.search import index_text


async def main() -> None:
    data = dump.parse(str(settings.legacy_dump), {"flarum_posts"})
    cols = {name: i for i, name in enumerate(data["flarum_posts"][0])}

    async with SessionLocal() as session:
        uploads = {u: None for u in await session.scalars(select(Upload.uuid))}
        users = await username_map(session)

        changed = 0
        for row in data["flarum_posts"][1]:
            content = row[cols["content"]] or ""
            if "<YOUTUBE" not in content and "<BILIBILI" not in content:
                continue
            post = await session.get(Post, int(row[cols["id"]]))
            if post is None or 'class="embed"></div>' not in post.body_html:
                continue

            html = render_legacy_s9e(content, uploads)
            post.body_html, _ = link_mentions(html, users)
            post.search_text = index_text(post.body_html)
            changed += 1

        await session.commit()
        print(f"re-rendered {changed} posts")


if __name__ == "__main__":
    asyncio.run(main())
