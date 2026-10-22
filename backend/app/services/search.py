"""中文搜索用的文本处理。

分词交给 jieba（成熟的中文分词库），检索交给 PostgreSQL 的 tsvector/tsquery，
不在应用层自己实现倒排索引或相关度排序。
"""
import functools
import html
import re

import jieba
from markdown_it import MarkdownIt

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")
_md = MarkdownIt("commonmark", {"html": False})


@functools.lru_cache(maxsize=1)
def _init() -> None:
    jieba.initialize()


def plain_text(source: str) -> str:
    """帖子 HTML → 纯文本（去标签、还原实体、折叠空白）。"""
    text = _TAG.sub(" ", source or "")
    return _WS.sub(" ", html.unescape(text)).strip()


def segment(text: str) -> str:
    """切成空格分隔的词，PostgreSQL 的 simple 配置按空格分 token。"""
    _init()
    # 用精确模式：cut_for_search 会追加子词，导致文本重复（"翻出出来"）
    parts = [w.strip() for w in jieba.cut(text or "")]
    return " ".join(w for w in parts if w and not w.isspace())


def index_text(source: str) -> str:
    return segment(plain_text(source))


# 分词结果用空格分隔，展示时要把中日韩字符之间的空格去掉
_CJK = r"\u3000-\u303f\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff00-\uffef"
_CJK_SPACE = re.compile(rf"(?<=[{_CJK}])[ ]+(?=[{_CJK}])")


def join_cjk(text: str) -> str:
    """把 `最近 得 有空` 还原成 `最近得有空`，只影响显示。"""
    prev = None
    while prev != text:
        prev = text
        text = _CJK_SPACE.sub("", text)
    return text
