"""浏览器安全响应头（SECURITY 2.3）。

全部响应经 after_request 附加；HSTS 仅在 HTTPS（或反代标明 https）时发送。
CSP 刻意宽松：允许现有内联 script/style，不外置页面脚本。
"""

from __future__ import annotations

from flask import Flask, Request, Response, request

# 约 180 天；不加 includeSubDomains / preload
HSTS_VALUE = "max-age=15552000"

# 宽松 CSP：同源 + 内联；无 CDN / 外站脚本字体
CONTENT_SECURITY_POLICY = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self'; "
    "font-src 'self'; "
    "connect-src 'self'; "
    "form-action 'self'; "
    "base-uri 'self'; "
    "frame-ancestors 'none'; "
    "object-src 'none'"
)

_COMMON_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": CONTENT_SECURITY_POLICY,
}


def request_is_https(req: Request) -> bool:
    """本连接为 HTTPS，或 Nginx 等反代声明 X-Forwarded-Proto: https。"""
    if req.is_secure:
        return True
    forwarded = (req.headers.get("X-Forwarded-Proto") or "").split(",")[0].strip()
    return forwarded.lower() == "https"


def apply_security_headers(resp: Response, req: Request | None = None) -> Response:
    """给响应写上常用安全头；HTTPS 时再加 HSTS。"""
    for key, value in _COMMON_HEADERS.items():
        resp.headers[key] = value
    current = req if req is not None else request
    if request_is_https(current):
        resp.headers["Strict-Transport-Security"] = HSTS_VALUE
    return resp


def register_security_headers(app: Flask) -> None:
    """在 create_app 中注册 after_request。"""

    @app.after_request
    def _security_headers(resp: Response) -> Response:
        return apply_security_headers(resp)
