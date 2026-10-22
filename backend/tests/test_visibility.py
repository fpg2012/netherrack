from types import SimpleNamespace

from app.services.visibility import can_view


def test_guest_cannot_view_private() -> None:
    discussion = SimpleNamespace(is_public=False)
    assert can_view(discussion, None) is False


def test_guest_can_view_public() -> None:
    discussion = SimpleNamespace(is_public=True)
    assert can_view(discussion, None) is True


def test_logged_in_sees_everything() -> None:
    user = SimpleNamespace(id=1)
    assert can_view(SimpleNamespace(is_public=False), user) is True
