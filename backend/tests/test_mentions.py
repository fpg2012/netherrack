from app.services.mentions import escape_legacy, link_mentions

USERS = {"aaa": (4, "aaa"), "nth233": (2, "nth233"), "Water_Chika": (6, "Water_Chika")}


def test_links_known_username() -> None:
    html, ids = link_mentions("<p>你好 @aaa</p>", USERS)
    assert '<a class="mention" href="/u/4">@aaa</a>' in html
    assert ids == [4]


def test_ignores_email_and_unknown() -> None:
    html, ids = link_mentions("<p>a@b.com 和 @不存在</p>", USERS)
    assert "@aaa" not in html
    assert "<a" not in html
    assert ids == []


def test_does_not_touch_code_or_links() -> None:
    html, ids = link_mentions('<pre>@aaa</pre><a href="/x">@aaa</a><p>@aaa</p>', USERS)
    assert html.count('<a class="mention"') == 1
    assert ids == [4]


def test_longest_name_wins() -> None:
    html, _ = link_mentions("<p>@Water_Chika 你好</p>", USERS)
    assert 'href="/u/6">@Water_Chika</a>' in html


def test_escape_legacy() -> None:
    assert escape_legacy('@"aaa"#p229') == "@aaa"
