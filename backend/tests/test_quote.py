from types import SimpleNamespace

from app.services.quote import build_quote, plain_text


def test_plain_text_strips_tags() -> None:
    html = "<p>你好 <strong>世界</strong></p><p>第二段</p>"
    assert plain_text(html) == "你好 世界 第二段"


def test_plain_text_truncates() -> None:
    assert plain_text("<p>" + "字" * 400 + "</p>").endswith("…")


def test_build_quote() -> None:
    post = SimpleNamespace(
        number=3,
        body_html="<p>原文</p>",
        author=SimpleNamespace(username="nth233", nickname=None),
    )
    assert build_quote(post) == "> **nth233** 在 #3 写道：\n> 原文"


def test_build_quote_anonymous() -> None:
    post = SimpleNamespace(number=1, body_html="<p>x</p>", author=None)
    assert "匿名" in build_quote(post)
