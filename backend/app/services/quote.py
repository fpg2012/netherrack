"""引用块的生成。"""
import re

from app.models import Post

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


def plain_text(html: str, limit: int = 280) -> str:
    text = _WS.sub(" ", _TAG.sub(" ", html or "")).strip()
    return text[:limit] + ("…" if len(text) > limit else "")


def build_quote(post: Post) -> str:
    """返回 Markdown 引用块。post.author 依赖 joined 预加载，不会触发懒加载。"""
    name = "匿名" if post.author is None else (post.author.nickname or post.author.username)
    body = plain_text(post.body_html)
    lines = [f"> **{name}** 在 #{post.number} 写道："]
    lines += ["> " + line for line in body.splitlines()] if body else [">"]
    return "\n".join(lines)
