"""把迁移数据里的 @"name"#p123 清理成可点击的 @name。

可重复执行：只处理仍然带着 Flarum 原始格式的 mention。
"""
import asyncio
import re

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Post, User

SPAN = re.compile(r'<span class="mention">@"?([^"@<\s#]+)"?(?:#p\d+)?</span>')
PLAIN = re.compile(r'@"?([^"@<\s#]+)"?(?:#p\d+)?')


async def main() -> None:
    async with SessionLocal() as session:
        users = {
            username: user_id
            for user_id, username in await session.execute(select(User.id, User.username))
        }
        posts = (await session.scalars(
            select(Post).where(Post.body_html.like('%@%'))
        )).all()

        changed = 0
        for post in posts:
            if '"#' not in post.body_html:
                continue

            def span(match: re.Match[str]) -> str:
                name = match.group(1)
                user_id = users.get(name)
                if user_id is None:
                    return f'<span class="mention">@{name}</span>'
                return f'<a class="mention" href="/u/{user_id}">@{name}</a>'

            html = SPAN.sub(span, post.body_html)
            html = PLAIN.sub(lambda m: f"@{m.group(1)}", html)
            if html != post.body_html:
                post.body_html = html
                changed += 1

        await session.commit()
        print(f"updated {changed} posts")


if __name__ == "__main__":
    asyncio.run(main())
