from app.services.search import index_text, join_cjk, segment


def test_segment_chinese() -> None:
    tokens = segment("考研数学的高数部分").split()
    assert "考研" in tokens
    assert "数学" in tokens
    assert all(" " not in t for t in tokens)


def test_index_text_strips_html_and_entities() -> None:
    text = index_text("<p>a &gt; b</p><p>黑幕</p>")
    assert "&gt;" not in text
    assert ">" in text
    assert "黑幕" in text


def test_join_cjk_removes_token_spaces() -> None:
    assert join_cjk("最近 得 有空 的 时候") == "最近得有空的时候"
    # 中英之间、英文之间的空格要保留
    assert join_cjk("flarum 搜索") == "flarum 搜索"
    assert join_cjk("hello world") == "hello world"
