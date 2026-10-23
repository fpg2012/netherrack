from app.services.events import publish, subscribe, unsubscribe


def test_publish_only_reaches_target_user() -> None:
    a = subscribe(1)
    b = subscribe(2)
    try:
        publish(1)
        assert a.get_nowait() is None
        assert b.empty()
    finally:
        unsubscribe(1, a)
        unsubscribe(2, b)


def test_unsubscribe_stops_delivery() -> None:
    q = subscribe(3)
    unsubscribe(3, q)
    publish(3)
    assert q.empty()
