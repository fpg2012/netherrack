"""解析 s9e TextFormatter 的帖子内容。

Flarum 把 `<r><p>…</p><URL url="…"><s>[</s>text<e>](…)</e></URL></r>` 这样的
XML 存在 posts.content 里。这里用 XML 解析器建树后遍历，而不是拿正则去改
标签 —— 标签是嵌套的，正则处理不了配对。

对外只暴露两个函数：
    to_html(xml) -> str    给 web 用
    to_text(xml) -> str    给终端用
解析失败（少数帖子的 content 是裸 JSON 或非法 XML）时退化成纯文本。
"""
import html
import re
import xml.etree.ElementTree as ET

# <s>/<e> 包住的是 BBCode 的语法标记（"[math:0]"、"**"、"!["），渲染时连内容一起丢
MARKER = {"S", "E"}

# 只是容器，输出时透明穿过
TRANSPARENT = {"R", "T", "ESC", "C", "FONT", "COLOR", "SPOILER", "DETAILS",
               "SUMMARY", "HR", "BR"}

INLINE = {"B": "strong", "STRONG": "strong", "I": "em", "EM": "em", "U": "u",
          "DEL": "del", "INS": "ins", "SUP": "sup", "SUB": "sub"}

HEADING = {"H1": 1, "H2": 2, "H3": 3, "H4": 4, "H5": 5, "H6": 6}


def _plain(el):
    """节点的纯文本内容（丢弃所有标签），给 code 块用。"""
    if (el.tag or "").upper() in MARKER:
        return ""
    out = el.text or ""
    for child in el:
        out += _plain(child) + (child.tail or "")
    return out


_ABS = re.compile(r"https?://[^/\s\"']+/assets/")


def _local(url):
    """把各个子域下的 /assets/ 绝对地址改写成本站 /media/。"""
    return _ABS.sub("/media/", url or "")


def _text(el):
    return html.escape(el.text or "", quote=False)


def _esc(s):
    return html.escape(s or "", quote=False)


def _walk(el, mode, uploads=None):
    """返回该节点及其子树的渲染结果。"""
    tag = (el.tag or "").upper()

    if tag in MARKER:
        return ""

    inner = _text(el)
    for child in el:
        inner += _emit(child, mode, uploads) + _esc(child.tail)

    if tag in TRANSPARENT:
        if tag == "BR":
            return "<br>" if mode == "html" else "\n"
        if tag == "HR":
            return "<hr>" if mode == "html" else "\n---\n"
        return inner

    if tag in INLINE:
        if mode == "html":
            t = INLINE[tag]
            return f"<{t}>{inner}</{t}>"
        return inner

    if tag in HEADING:
        n = HEADING[tag]
        if mode == "html":
            return f"<h{n}>{inner}</h{n}>"
        return f"\n{'#' * n} {inner}\n"

    if tag == "P":
        return f"<p>{inner}</p>" if mode == "html" else "\n" + inner + "\n"

    if tag == "URL":
        url = _local(el.get("url"))
        label = inner or _esc(url)
        if mode == "html":
            return f'<a href="{_esc(url)}" target="_blank" rel="noopener noreferrer">{label}</a>'
        return label if url in label else f"{label} ({url})"

    if tag == "IMG":
        src, alt = _local(el.get("src")), el.get("alt") or ""
        if mode == "html":
            return f'<img src="{_esc(src)}" alt="{_esc(alt)}" loading="lazy">'
        return f"![{alt}]({src})"

    if tag == "CODE":
        if mode == "html":
            # code 里不能留行内标签，取纯文本再转义
            body = _plain(el).strip("\n")
            return f"<pre><code>{html.escape(body, quote=False)}</code></pre>"
        body = inner.strip("\n")
        return f"\n```\n{body}\n```\n"

    if tag == "QUOTE":
        author = el.get("author") or ""
        lead = ""
        if author:
            lead = f"{_esc(author) if mode == 'html' else author} 写道："
        if mode == "html":
            return f"<blockquote>{lead}{inner}</blockquote>"
        body = "\n".join("> " + ln for ln in inner.strip().splitlines())
        return f"\n{lead}\n{body}\n"

    if tag == "LIST":
        ordered = (el.get("type") or "").lower() in {
            "decimal", "lower-alpha", "upper-alpha", "lower-roman",
        }
        if mode == "html":
            t = "ol" if ordered else "ul"
            return f"<{t}>{inner}</{t}>"
        return "\n" + inner + "\n"

    if tag == "LI":
        return f"<li>{inner}</li>" if mode == "html" else f"  - {inner.strip()}\n"

    if tag in {"TABLE", "THEAD", "TBODY", "TR", "TD", "TH"}:
        if mode == "html":
            if tag == "TABLE":
                return f'<table class="tbl">{inner}</table>'
            return f"<{tag.lower()}>{inner}</{tag.lower()}>"
        return inner + ("\n" if tag == "TR" else "  ")

    if tag in {"MATH", "IMATH"}:
        body = html.unescape(inner).strip()
        if mode == "html":
            # data-tex 存原始 LaTeX，前端用 KaTeX 渲染；元素内的文本作为降级显示
            attr = html.escape(body, quote=True)
            if tag == "MATH":
                return f'<div class="math-display" data-tex="{attr}">{_esc(body)}</div>'
            return f'<span class="math-inline" data-tex="{attr}">{_esc(body)}</span>'
        return f"\n{body}\n" if tag == "MATH" else body

    if tag == "POSTMENTION":
        mention = inner or el.get("username") or ""
        mention = mention if mention.startswith("@") else "@" + mention
        return f'<span class="mention">{mention}</span>' if mode == "html" else mention

    if tag == "UPL-IMAGE-PREVIEW":
        url = _local(el.get("url"))
        return f'<img src="{_esc(url)}" alt="" loading="lazy">' if mode == "html" \
            else f"![]({url})"

    if tag in {"UPL-FILE", "UPL-AUDIO", "UPL-VIDEO", "UPL-TEXT-PREVIEW"}:
        rec = (uploads or {}).get(el.get("uuid"))
        name = el.get("content") or (rec["base_name"] if rec else "") or inner
        size = el.get("size") or ""
        url = f"/media/files/{rec['path']}" if rec else _local(el.get("url"))
        label = f"{name} {size}".strip()
        if mode == "html":
            return f'<a class="upload" href="{_esc(url)}">{_esc(label)}</a>'
        return f"📎 {label} ({url})"

    if tag == "UPL":
        return f'<span class="upload">📎 {inner}</span>' if mode == "html" else f"📎 {inner}"

    # 视频嵌入
    if tag == "YOUTUBE":
        vid = el.get("id") or ""
        src = f"https://www.youtube-nocookie.com/embed/{vid}"
        if mode == "html":
            return (f'<div class="embed"><iframe src="{_esc(src)}" loading="lazy" '
                    'allowfullscreen frameborder="0"></iframe></div>')
        return f"▶ https://www.youtube.com/watch?v={vid}"

    if tag == "BILIBILI":
        bv = el.get("bvid") or ""
        src = f"https://player.bilibili.com/player.html?bvid={bv}&autoplay=0"
        if mode == "html":
            return (f'<div class="embed"><iframe src="{_esc(src)}" loading="lazy" '
                    'allowfullscreen frameborder="0"></iframe></div>')
        return f"▶ https://www.bilibili.com/video/{bv}"

    # 外部内容：只给链接，不嵌入
    if tag in {"TWITTER", "REDDIT", "GIST", "MEDIUM"}:
        return inner

    if tag == "USERMENTION":
        name = inner or ("@" + (el.get("displayname") or ""))
        return f'<span class="mention">{name}</span>' if mode == "html" else name

    if tag == "TASK":
        # 标签内容本身就是 "[ ]" 或 "[x]"，别再加一遍
        label = inner.strip()
        if label.startswith("["):
            return label
        return "[x] " + label if (el.get("state") or "") == "checked" else "[ ] " + label

    if tag == "ISPOILER":
        return f'<span class="spoiler">{inner}</span>' if mode == "html" else inner

    # 不认识的标签：只保留内容
    return inner


def _emit(el, mode, uploads=None):
    return _walk(el, mode, uploads)


def _render(xml, mode, uploads=None):
    if not xml:
        return ""
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        # 少数 content 是裸 JSON 或非法 XML，退化成纯文本
        return html.escape(xml) if mode == "html" else xml
    out = _walk(root, mode, uploads)
    if mode == "html":
        return out.strip()
    out = out.replace("\r\n", "\n")
    lines = [ln.rstrip() for ln in out.splitlines()]
    text = "\n".join(lines)
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
    return text.strip()


def to_html(xml, uploads=None):
    return _render(xml, "html", uploads)


def to_text(xml, uploads=None):
    return _render(xml, "text", uploads)
