"""HTTP 路由。"""

from __future__ import annotations

import json
import logging
import re
import time
import uuid
from pathlib import Path
from zipfile import BadZipFile

from docx.opc.exceptions import PackageNotFoundError
from flask import Blueprint, current_app, jsonify, request, send_file

from word_retrieval.csrf import issue_csrf_token, validate_csrf_token
from word_retrieval.ecdict import EcdictError, load_ecdict_headwords, lookup_definitions
from word_retrieval.extractor import extract_english_words, read_docx_text
from word_retrieval.highlighter import build_highlighted_docx
from word_retrieval.inflections import expand_wordlist_forms
from word_retrieval.job_cache import (
    TOKEN_RE,
    CacheLimitError,
    cleanup_expired,
    delete_download,
    delete_session_files,
    ensure_cache_capacity,
    get_download,
    pop_session,
    put_session,
    read_session_source_bytes,
    save_session,
    store_download,
)
from word_retrieval.lexicon import (
    decode_upload_text,
    ensure_wordlists_dir,
    list_wordlists,
    parse_and_validate_wordlist_text,
)
from word_retrieval.pages.confirm import render_confirm_page
from word_retrieval.pages.message import render_message_page
from word_retrieval.pages.privacy import render_privacy_page
from word_retrieval.pages.result import render_result_page
from word_retrieval.pages.settings import render_settings_page
from word_retrieval.user_data import (
    apply_confirm_updates,
    client_dict_entries_map,
    client_dict_overrides,
    dump_user_data,
    get_highlight,
    get_vocab_output,
    is_custom_wordlist,
    parse_user_data,
    resolve_known_words,
)
from word_retrieval.vocab_doc import build_vocabulary_docx

bp = Blueprint("main", __name__)
logger = logging.getLogger(__name__)

_ECDICT_PUBLIC_ERROR = "服务器缺少大词典，请联系管理员。"
_CSRF_FAIL_MESSAGE = "请求未通过安全校验，请从本站页面重新提交。"


def _safe_public_message(exc: BaseException, *, fallback: str) -> str:
    """业务 ValueError（含 CacheLimitError）可对外；其余只写日志并返回短文案。"""
    if isinstance(exc, ValueError):
        return str(exc)
    logger.exception("%s", fallback)
    return fallback


def _session_dir() -> Path:
    return Path(current_app.config["SESSION_DIR"])


def _download_dir() -> Path:
    return Path(current_app.config["DOWNLOAD_DIR"])


def _cache_max_age() -> float:
    return float(current_app.config["CACHE_MAX_AGE_SEC"])


def _cleanup_job_cache() -> None:
    cleanup_expired(
        _session_dir(),
        _download_dir(),
        max_age_sec=_cache_max_age(),
    )


def _safe_stem(filename: str) -> str:
    stem = Path(filename).stem
    stem = re.sub(r"[^\w\-]+", "_", stem, flags=re.UNICODE).strip("_")
    return stem or "document"


def _issue_csrf() -> str:
    return issue_csrf_token(
        current_app.config["CSRF_SECRET"],
        max_age_sec=int(current_app.config["CSRF_TOKEN_MAX_AGE_SEC"]),
    )


def _csrf_ok() -> bool:
    return validate_csrf_token(
        current_app.config["CSRF_SECRET"],
        request.form.get("csrf_token"),
        max_age_sec=int(current_app.config["CSRF_TOKEN_MAX_AGE_SEC"]),
    )


def _require_csrf_page():
    """表单页 POST：失败返回 403 提示页，成功返回 None。"""
    if _csrf_ok():
        return None
    return render_message_page("安全校验失败", _CSRF_FAIL_MESSAGE, status=403)


def _require_csrf_json():
    """JSON API POST：失败返回 403 JSON，成功返回 None。"""
    if _csrf_ok():
        return None
    return (
        jsonify({"ok": False, "error": _CSRF_FAIL_MESSAGE}),
        403,
    )


def _store_download(content: bytes, download_name: str) -> str:
    ensure_cache_capacity(
        _session_dir(),
        _download_dir(),
        max_age_sec=_cache_max_age(),
        max_bytes=int(current_app.config["CACHE_MAX_BYTES"]),
        extra_bytes=len(content) + 256,
    )
    return store_download(_download_dir(), content, download_name)


def _wordlists_dir() -> Path:
    return Path(current_app.config["WORDLISTS_DIR"])


def _baseline_names() -> list[str]:
    return list_wordlists(_wordlists_dir())


def _render_index() -> str:
    html = Path(current_app.config["INDEX_HTML"]).read_text(encoding="utf-8")
    names = _baseline_names()
    # 仅注入服务器基准表；自建表由前端 localStorage 合并
    options = []
    for name in names:
        options.append(f'<option value="{name}">{name}</option>')
    options_html = "\n          ".join(options)
    baseline_json = json.dumps(names, ensure_ascii=False)
    html = html.replace("<!--WORDLIST_OPTIONS-->", options_html)
    html = html.replace("<!--BASELINE_WORDLISTS_JSON-->", baseline_json)
    return html.replace("<!--CSRF_TOKEN-->", _issue_csrf())


def _classification_dictionary(user_data: dict) -> frozenset[str]:
    """黄/红分类：ECDICT ∪ 用户增补 − 用户排除（不读服务器共享覆盖文件）。"""
    db = Path(current_app.config["ECDICT_DB"])
    base = set(load_ecdict_headwords(str(db)))
    extra, exclude = client_dict_overrides(user_data)
    return frozenset((base | extra) - exclude)


def _begin_review(
    text: str,
    *,
    source_label: str,
    wordlist_name: str,
    user_data: dict,
    highlight_bytes: bytes | None = None,
    stem: str = "article",
):
    max_source = int(current_app.config["MAX_SOURCE_TEXT_CHARS"])
    if len(text) > max_source:
        return render_message_page(
            "文本过长",
            f"合并后的文本不得超过 {max_source} 个字符，请缩短后重试。",
            status=400,
        )

    words = extract_english_words(text)
    max_words = int(current_app.config["MAX_EXTRACTED_WORDS"])
    if len(words) > max_words:
        return render_message_page(
            "词数过多",
            f"提取到的不重复单词为 {len(words)} 个，超过上限 {max_words}，请缩短文章后重试。",
            status=400,
        )

    dict_path = Path(current_app.config["ECDICT_DB"])
    if not dict_path.exists():
        return render_message_page(
            "缺少大词典",
            f"未找到 ECDICT 数据库 {dict_path.name}。请运行 build_ecdict_db.py 生成。",
            status=500,
        )

    baseline = _baseline_names()
    try:
        if not is_custom_wordlist(user_data, wordlist_name):
            # 触发「对照表不存在」等错误
            from word_retrieval.lexicon import resolve_wordlist_path

            resolve_wordlist_path(_wordlists_dir(), wordlist_name)
        known = resolve_known_words(user_data, wordlist_name, _wordlists_dir())
    except ValueError as exc:
        return render_message_page("对照表错误", str(exc), status=400)
    except Exception as exc:  # noqa: BLE001
        msg = _safe_public_message(
            exc, fallback="对照表不可用，请检查名称或本机数据后重试。"
        )
        return render_message_page("对照表错误", msg, status=400)

    try:
        dictionary = _classification_dictionary(user_data)
    except EcdictError as exc:
        logger.exception("ECDICT 不可用: %s", exc)
        return render_message_page("缺少大词典", _ECDICT_PUBLIC_ERROR, status=500)

    from word_retrieval.lexicon import classify_words

    green, yellow, red = classify_words(words, known=known, dictionary=dictionary)

    print("=" * 40)
    print(f"来源: {source_label}")
    print(f"对照表: {wordlist_name}（用户差分已合并）")
    print(f"总计 {len(words)} | 绿 {len(green)} | 黄 {len(yellow)} | 红 {len(red)}")
    print("=" * 40)

    try:
        ensure_cache_capacity(
            _session_dir(),
            _download_dir(),
            max_age_sec=_cache_max_age(),
            max_sessions=int(current_app.config["CACHE_MAX_SESSIONS"]),
            max_bytes=int(current_app.config["CACHE_MAX_BYTES"]),
            extra_bytes=len(highlight_bytes or b"") + 4096,
            require_session_slot=True,
        )
    except CacheLimitError as exc:
        return render_message_page("暂时无法处理", str(exc), status=503)

    session_id = uuid.uuid4().hex
    session = {
        "created_at": time.time(),
        "source_label": source_label,
        "stem": stem,
        "wordlist_name": wordlist_name,
        "user_data": user_data,
        "baseline_names": baseline,
        "green": green,
        "yellow": yellow,
        "red": red,
        "source_path": None,
    }
    save_session(
        _session_dir(),
        session_id,
        session,
        source_bytes=highlight_bytes,
    )
    return render_confirm_page(
        session_id=session_id,
        source_label=source_label,
        wordlist_name=wordlist_name,
        green_words=green,
        yellow_words=yellow,
        red_words=red,
        highlight=get_highlight(user_data),
        csrf_token=_issue_csrf(),
    )


def _finalize_session(
    session: dict,
    *,
    session_id: str | None = None,
    green_to_vocab: set[str],
    green_remove_words: set[str],
    yellow_to_words: set[str],
    yellow_to_dict: set[str],
    yellow_dict_entries: list[dict] | None = None,
    keep_red: set[str],
    red_to_words: set[str],
):
    wordlist_name = session["wordlist_name"]
    user_data = session["user_data"]
    baseline_names = set(session.get("baseline_names") or _baseline_names())

    green_to_vocab &= set(session["green"])
    green_remove_words &= set(session["green"])
    yellow_to_words &= set(session["yellow"])
    yellow_to_dict &= set(session["yellow"])
    keep_red &= set(session["red"])
    red_to_words &= set(session["red"])

    try:
        updated_user_data, saved_count, removed_count = apply_confirm_updates(
            user_data,
            wordlist_name=wordlist_name,
            baseline_names=baseline_names,
            green_remove_words=green_remove_words,
            yellow_to_words=yellow_to_words,
            yellow_to_dict=yellow_to_dict,
            yellow_dict_entries=yellow_dict_entries,
            red_to_words=red_to_words,
        )
    except ValueError as exc:
        if session_id:
            session["created_at"] = time.time()
            put_session(_session_dir(), session_id, session)
        return render_message_page("确认失败", str(exc), status=400)

    # 文档着色：剔出对照表的绿词按未掌握（红）显示
    doc_green = (
        (set(session["green"]) - green_remove_words) | yellow_to_words | red_to_words
    )
    moved_to_dict_only = yellow_to_dict - yellow_to_words - doc_green
    doc_red = (set(session["red"]) | moved_to_dict_only | green_remove_words) - doc_green
    doc_yellow = set(session["yellow"]) - yellow_to_dict - yellow_to_words

    stem = session["stem"]
    source_label = session["source_label"]

    highlight_token = None
    highlight_name = None
    highlight_bytes = read_session_source_bytes(session)
    if session_id:
        delete_session_files(_session_dir(), session_id)
    if highlight_bytes is not None:
        try:
            highlighted = build_highlighted_docx(
                highlight_bytes,
                green=doc_green,
                yellow=doc_yellow,
                red=doc_red,
                highlight=get_highlight(updated_user_data),
            )
        except Exception as exc:  # noqa: BLE001
            msg = _safe_public_message(
                exc, fallback="文档着色失败，请稍后重试或换一份文档。"
            )
            return render_message_page("处理失败", msg, status=500)
        highlight_name = f"{stem}_highlighted.docx"
        try:
            highlight_token = _store_download(highlighted, highlight_name)
        except CacheLimitError as exc:
            return render_message_page("暂时无法处理", str(exc), status=503)

    vocab_words = keep_red | green_to_vocab

    translate_error = None
    vocab_token = None
    vocab_name = f"{stem}_unknown_vocab.docx"
    try:
        sorted_vocab = sorted(vocab_words)
        definitions = lookup_definitions(
            sorted_vocab,
            Path(current_app.config["ECDICT_DB"]),
            client_entries=client_dict_entries_map(updated_user_data),
            vocab_output=get_vocab_output(updated_user_data),
        )
        pairs: list[tuple[str, str]] = []
        for word in sorted_vocab:
            text = definitions.get(word)
            if text is None:
                pairs.append((word, "（词库未收录）"))
            else:
                pairs.append((word, text))
        missing = sum(1 for _, text in pairs if text == "（词库未收录）")
        if missing and sorted_vocab:
            translate_error = (
                f"ECDICT 未命中 {missing}/{len(sorted_vocab)} 个词，"
                "已在释义表中标注「词库未收录」。"
            )
        vocab_token = _store_download(build_vocabulary_docx(pairs), vocab_name)
    except CacheLimitError as exc:
        return render_message_page("暂时无法处理", str(exc), status=503)
    except EcdictError as exc:
        logger.exception("查词 ECDICT 不可用: %s", exc)
        translate_error = _ECDICT_PUBLIC_ERROR
        pairs = [(word, "") for word in sorted(vocab_words)]
        try:
            vocab_token = _store_download(build_vocabulary_docx(pairs), vocab_name)
        except CacheLimitError as limit_exc:
            return render_message_page("暂时无法处理", str(limit_exc), status=503)
    except Exception as exc:  # noqa: BLE001
        translate_error = _safe_public_message(
            exc, fallback="查词过程出错，释义表可能不完整，请稍后重试。"
        )
        pairs = [(word, "") for word in sorted(vocab_words)]
        try:
            vocab_token = _store_download(build_vocabulary_docx(pairs), vocab_name)
        except CacheLimitError as limit_exc:
            return render_message_page("暂时无法处理", str(limit_exc), status=503)

    known = resolve_known_words(updated_user_data, wordlist_name, _wordlists_dir())
    try:
        dictionary = _classification_dictionary(updated_user_data)
    except EcdictError:
        dictionary = frozenset()
    all_words = set(session["green"]) | set(session["yellow"]) | set(session["red"])
    from word_retrieval.lexicon import classify_words

    green, yellow, _red = classify_words(all_words, known=known, dictionary=dictionary)

    return render_result_page(
        source_label=f"{source_label}（对照表 {wordlist_name}）",
        green_words=green,
        yellow_words=yellow,
        red_words=vocab_words,
        highlight_token=highlight_token,
        highlight_name=highlight_name,
        vocab_token=vocab_token,
        vocab_name=vocab_name,
        translate_error=translate_error,
        saved_count=saved_count,
        removed_count=removed_count,
        user_data_json=dump_user_data(updated_user_data),
        highlight=get_highlight(updated_user_data),
    )


@bp.get("/")
def index():
    ensure_wordlists_dir(
        _wordlists_dir(),
        legacy_words=Path(current_app.config["LEGACY_WORDS_TXT"]),
    )
    return _render_index()


@bp.get("/settings")
def settings():
    ensure_wordlists_dir(
        _wordlists_dir(),
        legacy_words=Path(current_app.config["LEGACY_WORDS_TXT"]),
    )
    names = _baseline_names()
    return render_settings_page(
        baseline_wordlists=names,
        csrf_token=_issue_csrf(),
    )


@bp.get("/privacy")
def privacy():
    return render_privacy_page()


@bp.get("/healthz")
def healthz():
    """轻量存活检查：不加载 ECDICT、不扫缓存。"""
    return jsonify({"ok": True})


@bp.post("/api/parse_wordlist")
def api_parse_wordlist():
    """
    校验上传的对照表 txt，可选扩展派生词；结果由前端写入 localStorage。

    表单参数：
      use_ecdict_exchange=1 — 采信 ECDICT exchange（默认开启若未传则看该字段）
      algo_mode=none|all|pick — 算法扩充策略
    """
    denied = _require_csrf_json()
    if denied is not None:
        return denied

    uploaded = request.files.get("wordlist_file")
    if uploaded is None or not uploaded.filename:
        return jsonify({"ok": False, "error": "请选择要上传的 .txt 文件。"}), 400
    filename = Path(uploaded.filename).name
    if not filename.lower().endswith(".txt"):
        return jsonify({"ok": False, "error": "仅支持 .txt 文件。"}), 400
    try:
        raw = uploaded.read()
        text = decode_upload_text(raw)
        words = parse_and_validate_wordlist_text(text)
        base_count = len(words)

        # 兼容旧前端：add_inflections=1 → ECDICT + 算法全部采信
        legacy = (request.form.get("add_inflections") or "") == "1"
        use_ecdict_raw = request.form.get("use_ecdict_exchange")
        if use_ecdict_raw is None:
            use_ecdict = legacy
        else:
            use_ecdict = use_ecdict_raw == "1"
        algo_mode = (request.form.get("algo_mode") or "").strip().lower()
        if not algo_mode:
            algo_mode = "all" if legacy else "none"
        if algo_mode not in {"none", "all", "pick"}:
            algo_mode = "none"

        if algo_mode in {"all", "pick"}:
            max_algo = int(current_app.config["MAX_ALGO_EXPAND_WORDS"])
            if base_count > max_algo:
                raise ValueError(
                    f"启用算法扩充时，基础词数不得超过 {max_algo}，"
                    f"当前为 {base_count}。请关闭算法或减少词数。"
                )

        if use_ecdict or algo_mode != "none":
            deadline = time.monotonic() + float(
                current_app.config["MAX_EXPAND_SEC"]
            )
            result = expand_wordlist_forms(
                words,
                ecdict_db=Path(current_app.config["ECDICT_DB"]),
                use_ecdict_exchange=use_ecdict,
                algo_mode=algo_mode,
                deadline=deadline,
            )
            return jsonify(
                {
                    "ok": True,
                    "words": result["accepted"],
                    "algo_candidates": result["algo_candidates"],
                    "base_count": base_count,
                    "total_count": len(result["accepted"]),
                    "ecdict_added": result["ecdict_added"],
                    "algo_trusted_count": result["algo_trusted_count"],
                    "algo_mode": result["algo_mode"],
                    "use_ecdict_exchange": result["use_ecdict_exchange"],
                    "needs_pick": result["needs_pick"],
                    "with_inflections": True,
                }
            )

        sorted_words = sorted(set(words))
        return jsonify(
            {
                "ok": True,
                "words": sorted_words,
                "algo_candidates": [],
                "base_count": base_count,
                "total_count": len(sorted_words),
                "ecdict_added": 0,
                "algo_trusted_count": 0,
                "algo_mode": "none",
                "use_ecdict_exchange": False,
                "needs_pick": False,
                "with_inflections": False,
            }
        )
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    except Exception as exc:  # noqa: BLE001
        msg = _safe_public_message(
            exc, fallback="解析失败，请检查文件格式后重试。"
        )
        return jsonify({"ok": False, "error": msg}), 400


@bp.post("/upload")
def upload():
    denied = _require_csrf_page()
    if denied is not None:
        return denied

    uploaded = request.files.get("document")
    article = (request.form.get("article") or "").strip()
    has_file = uploaded is not None and bool(uploaded.filename)
    wordlist_name = (request.form.get("wordlist") or "words.txt").strip()
    try:
        user_data = parse_user_data(request.form.get("user_data"))
    except ValueError as exc:
        return render_message_page("本机数据过大", str(exc), status=400)

    if not has_file and not article:
        return render_message_page(
            "未收到内容",
            "请上传 Word 文档，或在文本框中输入文章后再提交。",
        )

    max_article = int(current_app.config["MAX_ARTICLE_CHARS"])
    if len(article) > max_article:
        return render_message_page(
            "文本过长",
            f"粘贴文本不得超过 {max_article} 个字符，当前为 {len(article)}。",
            status=400,
        )

    if has_file:
        filename = Path(uploaded.filename).name
        if not filename.lower().endswith(".docx"):
            return render_message_page(
                "格式不支持",
                f"当前仅支持 .docx 文件，你上传的是：{filename}",
            )
        file_bytes = uploaded.read()
        try:
            doc_text = read_docx_text(
                file_bytes,
                max_entries=int(current_app.config["MAX_DOCX_ENTRIES"]),
                max_uncompressed=int(current_app.config["MAX_DOCX_UNCOMPRESSED"]),
                max_ratio=float(current_app.config["MAX_DOCX_RATIO"]),
            )
        except (BadZipFile, PackageNotFoundError):
            return render_message_page(
                "无法读取文档",
                "文件不是有效的 .docx（也可能是旧版 .doc）。请用 Word/WPS 另存为 .docx 后再试。",
            )
        except ValueError as exc:
            return render_message_page("无法处理文档", str(exc), status=400)
        except Exception as exc:  # noqa: BLE001
            msg = _safe_public_message(
                exc, fallback="服务器处理文档失败，请稍后重试。"
            )
            return render_message_page("处理失败", msg, status=500)

        combined = f"{doc_text}\n{article}" if article else doc_text
        source = filename if not article else f"{filename} + 文本输入"
        return _begin_review(
            combined,
            source_label=source,
            wordlist_name=wordlist_name,
            user_data=user_data,
            highlight_bytes=file_bytes,
            stem=_safe_stem(filename),
        )

    return _begin_review(
        article,
        source_label="文本输入",
        wordlist_name=wordlist_name,
        user_data=user_data,
        highlight_bytes=None,
        stem="article",
    )


@bp.post("/confirm")
def confirm():
    denied = _require_csrf_page()
    if denied is not None:
        return denied

    _cleanup_job_cache()
    session_id = (request.form.get("session_id") or "").strip()
    if not TOKEN_RE.fullmatch(session_id):
        return render_message_page("会话无效", "请重新提交文章或文档。", status=400)

    session = pop_session(_session_dir(), session_id)
    if session is None:
        return render_message_page(
            "会话已过期",
            "确认页已失效，请返回首页重新提取。",
            status=404,
        )

    green_to_vocab = {
        v.strip().lower() for v in request.form.getlist("green_to_vocab") if v.strip()
    }
    green_remove_words = {
        v.strip().lower()
        for v in request.form.getlist("green_remove_words")
        if v.strip()
    }
    yellow_to_words = {
        v.strip().lower() for v in request.form.getlist("yellow_to_words") if v.strip()
    }
    yellow_to_dict = {
        v.strip().lower() for v in request.form.getlist("yellow_to_dict") if v.strip()
    }
    keep_red = {v.strip().lower() for v in request.form.getlist("keep_red") if v.strip()}
    red_to_words = {
        v.strip().lower() for v in request.form.getlist("red_to_words") if v.strip()
    }

    yellow_dict_entries: list[dict] = []
    raw_entries = (request.form.get("yellow_dict_entries") or "").strip()
    if raw_entries:
        try:
            parsed = json.loads(raw_entries)
        except json.JSONDecodeError:
            return render_message_page(
                "确认失败",
                "大词典词条数据格式无效，请返回确认页重试。",
                status=400,
            )
        if not isinstance(parsed, list):
            return render_message_page(
                "确认失败",
                "大词典词条数据格式无效，请返回确认页重试。",
                status=400,
            )
        yellow_dict_entries = [e for e in parsed if isinstance(e, dict)]

    return _finalize_session(
        session,
        session_id=session_id,
        green_to_vocab=green_to_vocab,
        green_remove_words=green_remove_words,
        yellow_to_words=yellow_to_words,
        yellow_to_dict=yellow_to_dict,
        yellow_dict_entries=yellow_dict_entries,
        keep_red=keep_red,
        red_to_words=red_to_words,
    )


@bp.get("/download/<token>")
def download_file(token: str):
    from io import BytesIO

    if not TOKEN_RE.fullmatch(token):
        return render_message_page("无效链接", "下载链接无效。", status=404)

    _cleanup_job_cache()
    download_dir = _download_dir()
    meta = get_download(download_dir, token)
    if meta is None:
        return render_message_page(
            "文件已过期",
            "文档缓存已失效或已下载过（链接仅一次有效），请重新提交生成。",
            status=404,
        )

    path = Path(meta["path"]).resolve()
    try:
        path.relative_to(download_dir.resolve())
    except ValueError:
        delete_download(download_dir, token)
        return render_message_page(
            "文件已过期",
            "文档不存在，请重新提交生成。",
            status=404,
        )
    if not path.is_file():
        delete_download(download_dir, token)
        return render_message_page(
            "文件已过期",
            "文档不存在，请重新提交生成。",
            status=404,
        )

    # 先读入内存再删文件，避免 Windows 下发送中占用句柄；首次下载后删除
    try:
        payload = path.read_bytes()
    except OSError:
        delete_download(download_dir, token)
        return render_message_page(
            "文件已过期",
            "文档读取失败，请重新提交生成。",
            status=404,
        )
    download_name = meta["download_name"]
    delete_download(download_dir, token)

    return send_file(
        BytesIO(payload),
        as_attachment=True,
        download_name=download_name,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
