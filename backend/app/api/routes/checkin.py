from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentUser, SessionDep, verify_csrf
from app.core.ratelimit import limiter
from app.models import CheckIn
from app.schemas.checkin import CheckInStatus
from app.services.checkins import site_today, summarize

router = APIRouter(prefix="/checkin", tags=["checkin"])


async def _status(session: SessionDep, user_id: int) -> CheckInStatus:
    dates = (
        await session.scalars(
            select(CheckIn.checked_on).where(CheckIn.user_id == user_id)
        )
    ).all()
    return summarize(dates)


@router.get("", response_model=CheckInStatus)
async def get_checkin(session: SessionDep, viewer: CurrentUser) -> CheckInStatus:
    return await _status(session, viewer.id)


@router.post("", response_model=CheckInStatus, dependencies=[Depends(verify_csrf)])
@limiter.limit("10/hour")
async def do_checkin(
    request: Request, session: SessionDep, viewer: CurrentUser
) -> CheckInStatus:
    today = site_today()
    session.add(CheckIn(user_id=viewer.id, checked_on=today))
    try:
        await session.commit()
    except IntegrityError:
        # 并发或重复提交，唯一约束兜底
        await session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "今天已经签到过了") from None
    return await _status(session, viewer.id)
