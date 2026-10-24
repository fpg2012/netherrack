"""帖子正文的渲染与清洗。

新帖子存 Markdown，渲染成 HTML 后用 nh3 清洗；从 Flarum 迁移过来的正文已经是
s9e 的 HTML，直接入库，不再二次转换（避免信息丢失）。
"""
import html
import re
from urllib.parse import urlsplit

import nh3
from markdown_it import MarkdownIt

_md = (
    MarkdownIt("commonmark", {"html": False, "linkify": True, "typographer": True})
    .enable("table")
    .enable("strikethrough")
    .enable("linkify")
)

ALLOWED_TAGS = {
    "a", "p", "br", "em", "strong", "del", "code", "pre", "blockquote",
    "ul", "ol", "li", "h1", "h2", "h3", "h4", "h5", "h6", "hr",
    "table", "thead", "tbody", "tr", "th", "td", "img", "span", "div", "sup", "sub",
    "iframe",
}
ALLOWED_ATTRS = {
    "a": {"href", "target", "class"},
    "img": {"src", "alt", "loading", "class"},
    "span": {"class", "data-tex", "style"},
    "div": {"class", "style", "data-tex"},
    "iframe": {
        "src", "class", "title", "width", "height", "loading",
        "allow", "allowfullscreen", "frameborder", "referrerpolicy",
    },
    "code": {"class"},
    "pre": {"class"},
    "th": {"colspan", "rowspan"},
    "td": {"colspan", "rowspan"},
}


# 只允许视频站的内嵌播放器，其余 <iframe> 一律丢掉
EMBED_HOSTS = {"www.youtube-nocookie.com", "www.youtube.com", "player.bilibili.com"}
_IFRAME = re.compile(r"<iframe\b[^>]*>.*?</iframe>", re.I | re.S)
_IFRAME_SRC = re.compile(r'src="([^"]*)"')


def _safe_iframes(markup: str) -> str:
    def repl(match: re.Match[str]) -> str:
        src = _IFRAME_SRC.search(match.group(0))
        if src is None:
            return ""
        host = urlsplit(html.unescape(src.group(1))).hostname or ""
        return match.group(0) if host in EMBED_HOSTS else ""

    return _IFRAME.sub(repl, markup)


# 单独成段的 B 站 / YouTube 链接自动变成播放器
_YT_URL = re.compile(
    r"^https?://(?:www\.|m\.)?(?:youtube\.com/(?:watch\?(?:[^#]*&)?v=|shorts/|embed/)|youtu\.be/)"
    r"([A-Za-z0-9_-]{6,})"
)
_BI_URL = re.compile(r"^https?://(?:www\.)?bilibili\.com/video/(BV[A-Za-z0-9]+)")
_PARAGRAPH_LINK = re.compile(r'<p><a href="([^"]+)"[^>]*>[^<]*</a></p>')


def _embed(url: str) -> str | None:
    url = html.unescape(url)
    if match := _YT_URL.match(url):
        src = f"https://www.youtube-nocookie.com/embed/{match.group(1)}"
    elif match := _BI_URL.match(url):
        src = f"https://player.bilibili.com/player.html?bvid={match.group(1)}&autoplay=0"
    else:
        return None
    return (f'<div class="embed"><iframe src="{src}" loading="lazy" '
            'allowfullscreen frameborder="0"></iframe></div>')


def embed_videos(markup: str) -> str:
    """把「整段只有一个视频链接」的段落换成 iframe。"""
    return _PARAGRAPH_LINK.sub(lambda m: _embed(m.group(1)) or m.group(0), markup)


_IMG_TAG = re.compile(r"<img\b([^>]*)>", re.I)


def lazy_images(markup: str) -> str:
    """给正文图片补上浏览器原生懒加载属性（旧数据也覆盖）。"""
    def repl(match: re.Match[str]) -> str:
        attrs = match.group(1)
        if "loading=" not in attrs:
            attrs += ' loading="lazy"'
        if "decoding=" not in attrs:
            attrs += ' decoding="async"'
        return f"<img{attrs}>"

    return _IMG_TAG.sub(repl, markup)


def render_markdown(text: str) -> str:
    return lazy_images(_safe_iframes(nh3.clean(
        embed_videos(_md.render(text)),
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        link_rel="noopener noreferrer",
    )))


def render_legacy_s9e(xml: str, uploads: dict | None = None) -> str:
    from app.services.s9e import to_html

    return lazy_images(_safe_iframes(nh3.clean(
        to_html(xml, uploads),
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        link_rel="noopener noreferrer",
    )))


EVENT_TEXT = {
    "discussionRenamed": "将标题从「{0}」改为「{1}」",
    "discussionTagged": "修改了标签",
    "discussionStickied": "置顶了该讨论",
    "discussionLocked": "锁定了该讨论",
    "recipientsModified": "修改了参与者",
    "recipientLeft": "退出了该讨论",
    "discussionCollapsed": "折叠了该讨论",
}


def event_text(kind: str, payload: object, who: str, tag_names: dict[int, str]) -> str:
    if kind == "discussionRenamed":
        values = payload if isinstance(payload, list) else []
        old, new = (values + ["", ""])[:2]
        return f"{who} 将标题从「{old}」改为「{new}」"
    if kind == "discussionTagged":
        values = payload if isinstance(payload, list) else [[], []]
        added, removed = (values + [[], []])[:2]
        parts = []
        if added:
            parts.append("添加标签 " + "、".join(tag_names.get(i, str(i)) for i in added))
        if removed:
            parts.append("移除标签 " + "、".join(tag_names.get(i, str(i)) for i in removed))
        return f"{who} " + "，".join(parts) if parts else f"{who} 修改了标签"
    if kind == "discussionStickied":
        data = payload if isinstance(payload, dict) else {}
        return f"{who} {'置顶' if data.get('sticky') else '取消置顶'}了该讨论"
    if kind == "discussionLocked":
        data = payload if isinstance(payload, dict) else {}
        return f"{who} {'锁定' if data.get('locked') else '解锁'}了该讨论"
    if kind == "recipientsModified":
        return f"{who} 修改了参与者"
    if kind == "recipientLeft":
        return f"{who} 退出了该讨论"
    if kind == "discussionCollapsed":
        data = payload if isinstance(payload, dict) else {}
        return f"{who} {'折叠' if data.get('collapsed') else '取消折叠'}了该讨论"
    return f"{who} {kind}"


_BLOCK = re.compile(
    r"</?(p|div|br|li|ul|ol|pre|blockquote|h[1-6]|tr|td|th|table)[^>]*>", re.I
)


def plain_text(markup: str) -> str:
    """把正文 HTML 压成一行纯文本，用于列表摘要（不做分词）。"""
    text = _BLOCK.sub(" ", markup)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()
