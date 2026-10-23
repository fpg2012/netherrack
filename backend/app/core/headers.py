"""统一的安全响应头。

后端只发 JSON 和 /media 文件，所以这里的 CSP 可以很严；HTML 由前端/nginx
提供，对应的 CSP 写在 README 的部署章节里。
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings

# 允许的 iframe 来源：和内容清洗里的 EMBED_HOSTS 保持一致
FRAME_SRC = "https://www.youtube-nocookie.com https://www.youtube.com https://player.bilibili.com"

API_CSP = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"


def security_headers(path: str, is_https: bool) -> dict[str, str]:
    headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "same-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    }
    # 文档页要加载 CDN 脚本，给它留一条生路；其余接口一律最严
    if not path.startswith("/api/docs"):
        headers["Content-Security-Policy"] = API_CSP
    if is_https:
        headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return headers


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        is_https = request.url.scheme == "https" or settings.cookie_secure
        for key, value in security_headers(request.url.path, is_https).items():
            response.headers.setdefault(key, value)
        return response
