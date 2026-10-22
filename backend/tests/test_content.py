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


def test_iframe_only_from_video_hosts() -> None:
    from app.services.content import _safe_iframes

    ok = '<div class="embed"><iframe src="https://www.youtube-nocookie.com/embed/x"></iframe></div>'
    assert _safe_iframes(ok) == ok
    evil = '<iframe src="https://evil.example/x"></iframe>'
    assert _safe_iframes(evil) == ""
    # 伪装成子域也不行
    assert _safe_iframes('<iframe src="https://evil.example/?h=www.youtube.com"></iframe>') == ""


def test_video_links_become_embeds() -> None:
    from app.services.content import embed_videos

    youtube = '<p><a href="https://youtu.be/dQw4w9WgXcQ">x</a></p>'
    assert 'youtube-nocookie.com/embed/dQw4w9WgXcQ' in embed_videos(youtube)

    bili = '<p><a href="https://www.bilibili.com/video/BV1xx411c7mD">x</a></p>'
    assert 'player.bilibili.com/player.html?bvid=BV1xx411c7mD' in embed_videos(bili)


def test_non_standalone_or_non_video_links_stay_links() -> None:
    from app.services.content import embed_videos

    inline = '<p>看这个 <a href="https://youtu.be/dQw4w9WgXcQ">x</a> 很好</p>'
    assert embed_videos(inline) == inline
    other = '<p><a href="https://example.com/x">x</a></p>'
    assert embed_videos(other) == other
