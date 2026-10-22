"""@ 提及：把正文里的 @用户名 换成主页链接，并返回被提及的用户。"""
import re

from sqlalchemy import select

from app.models import User

# 先粗抓一个候选串，再用真实用户名做最长前缀匹配，避免把
# 邮箱里的 @、@media 之类误判，也避免"@aaa答案"这类紧贴中文的情况
_CANDIDATE = re.compile(r"@([A-Za-z0-9_\u4e00-\u9fff-]{1,64})")
_TAG = re.compile(r"<[^>]+>")
_SKIP = {"a", "code", "pre"}


def escape_legacy(text: str) -> str:
    """Flarum 的 @"name"#p123 还原成 @name。"""
    return re.sub(r'@"?([^"@\s#]+)"?(?:#p\d+)?', r"@\1", text)


def _name_at(candidate: str, names: set[str]) -> str | None:
    for size in range(len(candidate), 0, -1):
        if candidate[:size] in names:
            return candidate[:size]
    return None


def link_mentions(markup: str, users: dict[str, tuple[int, str]]) -> tuple[str, list[int]]:
    """返回 (替换后的 HTML, 被提及的用户 id)。"""
    if not users or "@" not in markup:
        return markup, []
    names = set(users)
    found: list[int] = []
    out: list[str] = []
    skip_depth = 0

    for chunk in re.split(r"(<[^>]+>)", markup):
        if chunk.startswith("<"):
            tag = chunk[1:].split()[0].strip("/>").lower()
            if tag in _SKIP:
                if chunk.startswith("</"):
                    skip_depth = max(0, skip_depth - 1)
                elif not chunk.endswith("/>"):
                    skip_depth += 1
            out.append(chunk)
            continue
        if skip_depth or "@" not in chunk:
            out.append(chunk)
            continue

        def repl(match: re.Match[str]) -> str:
            name = _name_at(match.group(1), names)
            if name is None:
                return match.group(0)
            user_id, display = users[name]
            if user_id not in found:
                found.append(user_id)
            return f'<a class="mention" href="/u/{user_id}">@{display}</a>'

        out.append(_CANDIDATE.sub(repl, chunk))

    return "".join(out), found


async def username_map(session) -> dict[str, tuple[int, str]]:
    rows = await session.execute(select(User.id, User.username, User.nickname))
    return {
        username: (user_id, nickname or username)
        for user_id, username, nickname in rows
    }


async def mentionable_users(session, discussion_id: int) -> dict[str, tuple[int, str]]:
    """本贴可 @ 的人：楼主 + 所有楼层作者 + 管理员。"""
    from sqlalchemy import or_, select

    from app.models import Discussion, Post

    author_id = await session.scalar(
        select(Discussion.author_id).where(Discussion.id == discussion_id)
    )
    participant_ids = set(
        await session.scalars(
            select(Post.author_id).where(
                Post.discussion_id == discussion_id, Post.author_id.is_not(None)
            )
        )
    )
    if author_id is not None:
        participant_ids.add(author_id)
    admin_ids = set(await session.scalars(select(User.id).where(User.is_admin.is_(True))))

    rows = await session.execute(
        select(User.id, User.username, User.nickname).where(
            or_(User.id.in_(participant_ids), User.id.in_(admin_ids))
        )
    )
    return {(username): (uid, nick or username) for uid, username, nick in rows}
