"""无状态 CSRF 令牌：HMAC(expiry)，不依赖 Flask session。"""

from __future__ import annotations

import hmac
import os
import secrets
import time
from hashlib import sha256
from pathlib import Path

DEFAULT_MAX_AGE_SEC = 7200


def ensure_csrf_secret(path: Path, env_value: str | None = None) -> str:
    """优先环境变量；否则读写 path（生成 32 字节 hex）。"""
    env = (env_value if env_value is not None else os.environ.get("WR_CSRF_SECRET") or "").strip()
    if env:
        return env

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        existing = path.read_text(encoding="utf-8").strip()
        if existing:
            return existing

    secret = secrets.token_hex(32)
    # 多 worker 竞态：已有内容则采用已有文件
    try:
        fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        try:
            os.write(fd, secret.encode("utf-8"))
        finally:
            os.close(fd)
        return secret
    except FileExistsError:
        existing = path.read_text(encoding="utf-8").strip()
        if existing:
            return existing
        path.write_text(secret, encoding="utf-8")
        return secret


def issue_csrf_token(secret: str, *, max_age_sec: int = DEFAULT_MAX_AGE_SEC) -> str:
    expiry = int(time.time()) + int(max_age_sec)
    mac = hmac.new(
        secret.encode("utf-8"),
        str(expiry).encode("utf-8"),
        sha256,
    ).hexdigest()
    return f"{expiry}.{mac}"


def validate_csrf_token(
    secret: str,
    token: str | None,
    *,
    max_age_sec: int = DEFAULT_MAX_AGE_SEC,
) -> bool:
    if not token or not isinstance(token, str):
        return False
    parts = token.split(".", 1)
    if len(parts) != 2:
        return False
    expiry_s, mac = parts
    if not expiry_s.isdigit() or not mac:
        return False
    try:
        expiry = int(expiry_s)
    except ValueError:
        return False
    now = int(time.time())
    # 允许签发时的 max_age 窗口：未过期，且不接受远超 max_age 的「未来」expiry（防随意改大）
    if expiry < now or expiry > now + int(max_age_sec) + 60:
        return False
    expected = hmac.new(
        secret.encode("utf-8"),
        expiry_s.encode("utf-8"),
        sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, mac)
