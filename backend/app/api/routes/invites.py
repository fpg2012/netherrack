from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import aliased

from app.api.deps import CurrentUser, SessionDep, verify_csrf
from app.core.ratelimit import limiter
from app.models import Invite, User
from app.schemas.invite import InviteCreate, InviteCreated, InviteOut
from app.services.audit import audit
from app.services.invites import generate_code, hash_code, hint

router = APIRouter(prefix="/invites", tags=["invites"])


def _require_admin(user: User) -> None:
    if not user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "仅管理员可以管理邀请码")


@router.post("", response_model=InviteCreated, status_code=201,
             dependencies=[Depends(verify_csrf)])
@limiter.limit("30/hour")
async def create_invite(payload: InviteCreate, request: Request, session: SessionDep,
                        user: CurrentUser) -> InviteCreated:
    _require_admin(user)
    code = generate_code()
    expires_at = (datetime.now(UTC) + timedelta(days=payload.expires_in_days)
                  if payload.expires_in_days else None)
    invite = Invite(
        code_hash=hash_code(code),
        hint=hint(code),
        note=payload.note,
        created_by=user.id,
        expires_at=expires_at,
    )
    session.add(invite)
    await session.flush()
    # 审计只记 id / hint，绝不记明文
    await audit(session, actor_id=user.id, action="invite.create",
                target_type="invite", target_id=invite.id, hint=invite.hint,
                expires_at=expires_at.isoformat() if expires_at else None)
    await session.commit()
    return InviteCreated(id=invite.id, code=code, expires_at=expires_at, note=invite.note)


@router.get("", response_model=list[InviteOut])
async def list_invites(session: SessionDep, user: CurrentUser) -> list[InviteOut]:
    _require_admin(user)
    creator = aliased(User)
    used_by = aliased(User)
    rows = (await session.execute(
        select(Invite, creator.username, used_by.username)
        .outerjoin(creator, creator.id == Invite.created_by)
        .outerjoin(used_by, used_by.id == Invite.used_by)
        .order_by(Invite.created_at.desc(), Invite.id.desc())
        .limit(200)
    )).all()

    now = datetime.now(UTC)
    out = []
    for invite, creator_name, used_name in rows:
        if invite.revoked_at is not None:
            state = "revoked"
        elif invite.used_at is not None:
            state = "used"
        elif invite.expires_at is not None and invite.expires_at < now:
            state = "expired"
        else:
            state = "active"
        out.append(InviteOut(
            id=invite.id, hint=invite.hint, note=invite.note, status=state,
            created_at=invite.created_at, expires_at=invite.expires_at,
            used_at=invite.used_at, used_by=used_name,
            created_by=creator_name, revoked_at=invite.revoked_at,
        ))
    return out


@router.delete("/{invite_id}", status_code=204, dependencies=[Depends(verify_csrf)])
async def revoke_invite(invite_id: int, session: SessionDep, user: CurrentUser) -> None:
    _require_admin(user)
    invite = await session.scalar(
        select(Invite).where(Invite.id == invite_id).with_for_update()
    )
    if invite is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "邀请码不存在")
    if invite.used_at is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "已使用的邀请码不能撤销")
    if invite.revoked_at is None:
        invite.revoked_at = datetime.now(UTC)
        await audit(session, actor_id=user.id, action="invite.revoke",
                    target_type="invite", target_id=invite.id, hint=invite.hint)
        await session.commit()
