"""结构化请求日志（SECURITY 3.2）。

JSON 一行一条写 stderr；每请求挂 request_id 并回写 X-Request-ID。
不记录粘贴正文 / user_data / 密钥。GET /healthz 不打 INFO 访问日志。
"""

from __future__ import annotations

import json
import logging
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from flask import Flask, Response, g, has_request_context, request

REQUEST_ID_HEADER = "X-Request-ID"
_REQUEST_ID_RE = re.compile(r"^[0-9a-fA-F-]{8,64}$")
_HEALTHZ_PATH = "/healthz"


class JsonFormatter(logging.Formatter):
    """把 LogRecord 打成单行 JSON（额外字段来自 record.__dict__ 中的已知键）。"""

    _SKIP = {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "message",
        "asctime",
        "taskName",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if has_request_context():
            rid = getattr(g, "request_id", None)
            if rid:
                payload.setdefault("request_id", rid)
        for key, value in record.__dict__.items():
            if key in self._SKIP or key.startswith("_"):
                continue
            if value is None:
                continue
            payload[key] = value
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


class _RequestIdFilter(logging.Filter):
    """无请求上下文时不强制 request_id；有则注入到 record。"""

    def filter(self, record: logging.LogRecord) -> bool:
        if has_request_context() and not getattr(record, "request_id", None):
            rid = getattr(g, "request_id", None)
            if rid:
                record.request_id = rid  # type: ignore[attr-defined]
        return True


def new_request_id(incoming: str | None = None) -> str:
    raw = (incoming or "").strip()
    if raw and _REQUEST_ID_RE.fullmatch(raw):
        return raw
    return uuid.uuid4().hex


def configure_logging(level: int = logging.INFO) -> None:
    """配置 word_retrieval 包日志为 JSON；幂等（重复调用不叠加 handler）。"""
    root_pkg = logging.getLogger("word_retrieval")
    root_pkg.setLevel(level)
    if any(isinstance(h.formatter, JsonFormatter) for h in root_pkg.handlers):
        return
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    handler.addFilter(_RequestIdFilter())
    root_pkg.addHandler(handler)
    # 避免冒泡到 root 再打一遍非 JSON
    root_pkg.propagate = False


def register_request_logging(app: Flask) -> None:
    """在 create_app 中注册：配置日志 + before/after_request。"""
    configure_logging()
    log = logging.getLogger("word_retrieval.request")

    @app.before_request
    def _assign_request_id() -> None:
        g.request_id = new_request_id(request.headers.get(REQUEST_ID_HEADER))
        g.request_started = time.perf_counter()

    @app.after_request
    def _finish_request_log(resp: Response) -> Response:
        rid = getattr(g, "request_id", None) or new_request_id()
        g.request_id = rid
        resp.headers[REQUEST_ID_HEADER] = rid

        path = request.path or ""
        if path == _HEALTHZ_PATH:
            return resp

        started = getattr(g, "request_started", None)
        duration_ms = (
            round((time.perf_counter() - started) * 1000, 2)
            if started is not None
            else None
        )
        log.info(
            "request",
            extra={
                "event": "request",
                "request_id": rid,
                "method": request.method,
                "path": path,
                "status": resp.status_code,
                "duration_ms": duration_ms,
            },
        )
        return resp
