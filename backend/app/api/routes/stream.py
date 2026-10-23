import asyncio
import json

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.api.deps import CurrentUser
from app.services.events import subscribe, unsubscribe

router = APIRouter(tags=["stream"])

HEARTBEAT = 20  # 秒；比常见的 60s 代理超时短，防止连接被静默掐断


@router.get("/stream")
async def stream(request: Request, user: CurrentUser) -> StreamingResponse:
    """SSE：有新通知时推一条 notify 事件，前端据此刷新未读数。"""

    async def events():
        queue = subscribe(user.id)
        try:
            yield "retry: 5000\n\n"
            while True:
                try:
                    await asyncio.wait_for(queue.get(), timeout=HEARTBEAT)
                except TimeoutError:
                    if await request.is_disconnected():
                        break
                    yield ": ping\n\n"
                    continue
                if await request.is_disconnected():
                    break
                yield f"event: notify\ndata: {json.dumps({'unread': True})}\n\n"
        finally:
            unsubscribe(user.id, queue)

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            # 关掉 nginx 的缓冲，否则事件会被攒着发
            "X-Accel-Buffering": "no",
        },
    )
