"""操作审计：只记录，不提供删除/修改入口。"""
from app.models import AuditLog


async def audit(session, *, actor_id: int | None, action: str,
                target_type: str | None = None, target_id: int | None = None,
                **payload: object) -> None:
    session.add(AuditLog(
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        payload=payload or None,
    ))
