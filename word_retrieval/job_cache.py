"""当次处理会话与下载缓存（磁盘，跨 gunicorn worker 共享）。

布局：
  .cache/sessions/{id}.json
  .cache/sessions/{id}.src.docx   # 可选上传原文
  .cache/downloads/{token}.docx
  .cache/downloads/{token}.json
"""

from __future__ import annotations

import json
import re
import time
import uuid
from pathlib import Path
from typing import Any

TOKEN_RE = re.compile(r"^[0-9a-f]{32}$")
DEFAULT_MAX_AGE_SEC = 1800  # 30 分钟
DEFAULT_MAX_SESSIONS = 50
DEFAULT_MAX_CACHE_BYTES = 500 * 1024 * 1024  # 500 MB

_WORD_LIST_KEYS = ("green", "yellow", "red")


class CacheLimitError(ValueError):
    """会话数或缓存体积超限。"""


def ensure_cache_dirs(session_dir: Path, download_dir: Path) -> None:
    session_dir.mkdir(parents=True, exist_ok=True)
    download_dir.mkdir(parents=True, exist_ok=True)


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def _atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)


def _session_json_path(session_dir: Path, session_id: str) -> Path:
    return session_dir / f"{session_id}.json"


def _session_src_path(session_dir: Path, session_id: str) -> Path:
    return session_dir / f"{session_id}.src.docx"


def _download_docx_path(download_dir: Path, token: str) -> Path:
    return download_dir / f"{token}.docx"


def _download_meta_path(download_dir: Path, token: str) -> Path:
    return download_dir / f"{token}.json"


def _serialize_session(session: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {
        "created_at": float(session["created_at"]),
        "source_label": session["source_label"],
        "stem": session["stem"],
        "wordlist_name": session["wordlist_name"],
        "user_data": session["user_data"],
        "baseline_names": list(session.get("baseline_names") or []),
        "source_path": session.get("source_path"),
    }
    for key in _WORD_LIST_KEYS:
        value = session.get(key) or []
        out[key] = sorted(value) if isinstance(value, (set, frozenset)) else list(value)
    return out


def _deserialize_session(data: dict[str, Any]) -> dict[str, Any]:
    session: dict[str, Any] = {
        "created_at": float(data.get("created_at") or 0),
        "source_label": data.get("source_label") or "",
        "stem": data.get("stem") or "article",
        "wordlist_name": data.get("wordlist_name") or "words.txt",
        "user_data": data.get("user_data") if isinstance(data.get("user_data"), dict) else {},
        "baseline_names": list(data.get("baseline_names") or []),
        "source_path": data.get("source_path"),
    }
    for key in _WORD_LIST_KEYS:
        raw = data.get(key) or []
        if not isinstance(raw, list):
            raw = []
        session[key] = set(str(w).strip().lower() for w in raw if str(w).strip())
    return session


def _unlink(path: Path | None) -> None:
    if path is None:
        return
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def _read_created_at(meta_path: Path) -> float | None:
    try:
        data = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    try:
        return float(data.get("created_at") or 0)
    except (TypeError, ValueError):
        return None


def save_session(
    session_dir: Path,
    session_id: str,
    session: dict[str, Any],
    *,
    source_bytes: bytes | None = None,
) -> None:
    if not TOKEN_RE.fullmatch(session_id):
        raise ValueError("invalid session_id")
    session_dir.mkdir(parents=True, exist_ok=True)
    payload = dict(session)
    if source_bytes is not None:
        src_path = _session_src_path(session_dir, session_id)
        _atomic_write_bytes(src_path, source_bytes)
        payload["source_path"] = str(src_path)
    elif "source_path" not in payload:
        payload["source_path"] = None
    _atomic_write_text(
        _session_json_path(session_dir, session_id),
        json.dumps(_serialize_session(payload), ensure_ascii=False),
    )


def load_session(session_dir: Path, session_id: str) -> dict[str, Any] | None:
    if not TOKEN_RE.fullmatch(session_id):
        return None
    path = _session_json_path(session_dir, session_id)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return _deserialize_session(data)


def pop_session(session_dir: Path, session_id: str) -> dict[str, Any] | None:
    session = load_session(session_dir, session_id)
    if session is None:
        return None
    _unlink(_session_json_path(session_dir, session_id))
    # 原文文件留给 finalize 读取后再删；此处先保留 source_path
    return session


def put_session(session_dir: Path, session_id: str, session: dict[str, Any]) -> None:
    """确认失败时写回会话（不重写 source 字节；保留已有 source_path）。"""
    save_session(session_dir, session_id, session, source_bytes=None)


def delete_session_files(session_dir: Path, session_id: str) -> None:
    if not TOKEN_RE.fullmatch(session_id):
        return
    _unlink(_session_json_path(session_dir, session_id))
    _unlink(_session_src_path(session_dir, session_id))


def read_session_source_bytes(session: dict[str, Any]) -> bytes | None:
    source_path = session.get("source_path")
    if not source_path:
        return None
    path = Path(source_path)
    if not path.is_file():
        return None
    return path.read_bytes()


def count_active_sessions(session_dir: Path) -> int:
    if not session_dir.is_dir():
        return 0
    return sum(
        1
        for path in session_dir.glob("*.json")
        if TOKEN_RE.fullmatch(path.stem)
    )


def cache_total_bytes(session_dir: Path, download_dir: Path) -> int:
    total = 0
    for directory in (session_dir, download_dir):
        if not directory.is_dir():
            continue
        for path in directory.iterdir():
            if not path.is_file() or path.name.endswith(".tmp"):
                continue
            try:
                total += path.stat().st_size
            except OSError:
                continue
    return total


def ensure_cache_capacity(
    session_dir: Path,
    download_dir: Path,
    *,
    max_age_sec: float = DEFAULT_MAX_AGE_SEC,
    max_sessions: int | None = None,
    max_bytes: int | None = None,
    extra_bytes: int = 0,
    require_session_slot: bool = False,
) -> None:
    """清理过期项后检查上限；超限抛出 CacheLimitError。"""
    cleanup_expired(session_dir, download_dir, max_age_sec=max_age_sec)
    if require_session_slot and max_sessions is not None:
        if count_active_sessions(session_dir) >= max_sessions:
            raise CacheLimitError(
                "当前处理中的会话过多，请稍后再试，或等待约 30 分钟后过期清理。"
            )
    if max_bytes is not None:
        used = cache_total_bytes(session_dir, download_dir)
        if used + max(0, extra_bytes) > max_bytes:
            raise CacheLimitError(
                "服务器临时缓存已满，请稍后再试，或等待约 30 分钟后过期清理。"
            )


def store_download(download_dir: Path, content: bytes, download_name: str) -> str:
    download_dir.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex
    docx_path = _download_docx_path(download_dir, token)
    meta_path = _download_meta_path(download_dir, token)
    _atomic_write_bytes(docx_path, content)
    meta = {
        "path": str(docx_path),
        "download_name": download_name,
        "created_at": time.time(),
    }
    _atomic_write_text(meta_path, json.dumps(meta, ensure_ascii=False))
    return token


def get_download(download_dir: Path, token: str) -> dict[str, Any] | None:
    if not TOKEN_RE.fullmatch(token):
        return None
    meta_path = _download_meta_path(download_dir, token)
    if not meta_path.is_file():
        return None
    try:
        data = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    path_str = data.get("path") or str(_download_docx_path(download_dir, token))
    return {
        "path": path_str,
        "download_name": data.get("download_name") or "document.docx",
        "created_at": float(data.get("created_at") or 0),
    }


def delete_download(download_dir: Path, token: str) -> None:
    if not TOKEN_RE.fullmatch(token):
        return
    _unlink(_download_meta_path(download_dir, token))
    _unlink(_download_docx_path(download_dir, token))


def cleanup_expired(
    session_dir: Path,
    download_dir: Path,
    *,
    max_age_sec: float = DEFAULT_MAX_AGE_SEC,
) -> None:
    now = time.time()
    if session_dir.is_dir():
        for meta_path in session_dir.glob("*.json"):
            session_id = meta_path.stem
            if not TOKEN_RE.fullmatch(session_id):
                continue
            created = _read_created_at(meta_path)
            if created is None:
                try:
                    created = meta_path.stat().st_mtime
                except OSError:
                    continue
            if now - created > max_age_sec:
                delete_session_files(session_dir, session_id)
        # pop 后可能只剩原文；按 mtime 清孤儿
        for src_path in session_dir.glob("*.src.docx"):
            session_id = src_path.name[: -len(".src.docx")]
            if not TOKEN_RE.fullmatch(session_id):
                continue
            if _session_json_path(session_dir, session_id).is_file():
                continue
            try:
                mtime = src_path.stat().st_mtime
            except OSError:
                continue
            if now - mtime > max_age_sec:
                _unlink(src_path)

    if download_dir.is_dir():
        for meta_path in download_dir.glob("*.json"):
            token = meta_path.stem
            if not TOKEN_RE.fullmatch(token):
                continue
            created = _read_created_at(meta_path)
            if created is None:
                try:
                    created = meta_path.stat().st_mtime
                except OSError:
                    continue
            if now - created > max_age_sec:
                delete_download(download_dir, token)
        for docx_path in download_dir.glob("*.docx"):
            token = docx_path.stem
            if not TOKEN_RE.fullmatch(token):
                continue
            if _download_meta_path(download_dir, token).is_file():
                continue
            try:
                mtime = docx_path.stat().st_mtime
            except OSError:
                continue
            if now - mtime > max_age_sec:
                _unlink(docx_path)
