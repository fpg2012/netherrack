"""限流：用 slowapi（Starlette 集成），存储默认在进程内存。

单进程部署够用；多 worker 时要换成 Redis：
    Limiter(key_func=..., storage_uri="redis://127.0.0.1:6379")
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["300/minute"],
    # 关闭响应头注入：开启后 slowapi 要求每个被装饰的端点都声明 response 参数
    headers_enabled=False,
)
