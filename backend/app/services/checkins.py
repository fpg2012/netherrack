from collections.abc import Iterable
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.core.config import settings
from app.schemas.checkin import CheckInStatus


def site_today() -> date:
    """站点时区下的今天，签到按这个日期切分。"""
    return datetime.now(ZoneInfo(settings.timezone)).date()


def summarize(dates: Iterable[date], today: date | None = None) -> CheckInStatus:
    today = today or site_today()
    seen = set(dates)
    checked_today = today in seen

    # 今天还没签到时，昨天签过也算连续，直到今天结束
    cursor = today if checked_today else today - timedelta(days=1)
    streak = 0
    while cursor in seen:
        streak += 1
        cursor -= timedelta(days=1)

    return CheckInStatus(
        checked_in_today=checked_today,
        current_streak=streak,
        total_days=len(seen),
    )
