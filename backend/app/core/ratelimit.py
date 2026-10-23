"""限流：用 slowapi（Starlette 集成），存储默认在进程内存。

单进程部署够用；多 worker 时需要换成 Redis：
    Limiter(key_func=..., storage_uri="redis://127.0.0.1:6379")
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.core.config import settings


def client_ip(request: Request) -> str:
    """取客户端 IP。

    部署在反向代理后面时 request.client 是 127.0.0.1，所有用户会共用一个
    限流桶（一个人就能把全站的登录额度打满）。打开 TRUST_PROXY 后改读代理
    写入的 X-Forwarded-For / X-Real-IP。
    """
    if settings.trust_proxy:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
    return get_remote_address(request)


limiter = Limiter(
    key_func=client_ip,
    default_limits=["300/minute"],
    # 关闭响应头注入：开启后 slowapi 要求每个被装饰的端点都声明 response 参数
    headers_enabled=False,
)
