

def test_avatar_magic_bytes() -> None:
    from app.api.routes.users import _looks_like_image

    assert _looks_like_image(b"\x89PNG\r\n\x1a\n\x00\x00", ".png")
    assert _looks_like_image(b"\xff\xd8\xff\xe0", ".jpg")
    assert _looks_like_image(b"RIFF\x00\x00\x00\x00WEBPVP8 ", ".webp")
    assert not _looks_like_image(b"<html><body>", ".png")
    assert not _looks_like_image(b"\x89PNG\r\n\x1a\n", ".gif")
