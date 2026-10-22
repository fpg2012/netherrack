from app.services.content import render_markdown
from app.services.s9e import to_html


def test_math_kept_for_katex() -> None:
    html = to_html('<r><p><MATH><s>[math:0]</s>x^2<e>[/math:0]</e></MATH></p></r>')
    assert 'data-tex="x^2"' in html
    assert "math-display" in html


def test_marker_content_dropped() -> None:
    html = to_html('<r><p><URL url="https://e.com"><s>[</s>label<e>](https://e.com)</e></URL></p></r>')
    assert '<a href="https://e.com"' in html
    assert "label" in html
    assert "[math" not in html


def test_markdown_sanitized() -> None:
    html = render_markdown("# hi\n\n<script>alert(1)</script>")
    assert "<h1>hi</h1>" in html
    assert "<script" not in html


def test_plain_text_strips_tags_and_keeps_chinese() -> None:
    from app.services.content import plain_text

    html = '<p>中文<strong>加粗</strong>混排</p><p>第二段</p>'
    assert plain_text(html) == "中文加粗混排 第二段"


def test_plain_text_unescapes_entities() -> None:
    from app.services.content import plain_text

    assert plain_text("<p>a &amp; b&nbsp;c</p>") == "a & b c"
