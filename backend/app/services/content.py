"""帖子正文的渲染与清洗。

新帖子存 Markdown，渲染成 HTML 后用 nh3 清洗；从 Flarum 迁移过来的正文已经是
s9e 的 HTML，直接入库，不再二次转换（避免信息丢失）。
"""
import html
import re

import nh3
from markdown_it import MarkdownIt

_md = (
    MarkdownIt("commonmark", {"html": False, "linkify": True, "typographer": True})
    .enable("table")
    .enable("strikethrough")
)

ALLOWED_TAGS = {
    "a", "p", "br", "em", "strong", "del", "code", "pre", "blockquote",
    "ul", "ol", "li", "h1", "h2", "h3", "h4", "h5", "h6", "hr",
    "table", "thead", "tbody", "tr", "th", "td", "img", "span", "div", "sup", "sub",
}
ALLOWED_ATTRS = {
    "a": {"href", "target", "class"},
    "img": {"src", "alt", "loading", "class"},
    "span": {"class", "data-tex", "style"},
    "div": {"class", "style", "data-tex"},
    "code": {"class"},
    "pre": {"class"},
    "th": {"colspan", "rowspan"},
    "td": {"colspan", "rowspan"},
}


def render_markdown(text: str) -> str:
    return nh3.clean(
        _md.render(text),
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        link_rel="noopener noreferrer",
    )


def render_legacy_s9e(xml: str, uploads: dict | None = None) -> str:
    from app.services.s9e import to_html

    return nh3.clean(
        to_html(xml, uploads),
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        link_rel="noopener noreferrer",
    )


EVENT_TEXT = {
    "discussionRenamed": "将标题从「{0}」改为「{1}」",
    "discussionTagged": "修改了标签",
    "discussionStickied": "置顶了该讨论",
    "discussionLocked": "锁定了该讨论",
    "recipientsModified": "修改了参与者",
    "recipientLeft": "退出了该讨论",
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
    return f"{who} {kind}"


_BLOCK = re.compile(
    r"</?(p|div|br|li|ul|ol|pre|blockquote|h[1-6]|tr|td|th|table)[^>]*>", re.I
)


def plain_text(markup: str) -> str:
    """把正文 HTML 压成一行纯文本，用于列表摘要（不做分词）。"""
    text = _BLOCK.sub(" ", markup)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()
