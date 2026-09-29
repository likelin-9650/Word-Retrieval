"""HTTP 路由。"""

from __future__ import annotations

import json
import re
import time
import uuid
from pathlib import Path
from zipfile import BadZipFile

from docx.opc.exceptions import PackageNotFoundError
from flask import Blueprint, current_app, jsonify, request, send_file

from word_retrieval.ecdict import EcdictError, load_ecdict_headwords, lookup_definitions
from word_retrieval.extractor import extract_english_words, read_docx_text
from word_retrieval.highlighter import build_highlighted_docx
from word_retrieval.inflections import expand_with_inflections
from word_retrieval.lexicon import (
    decode_upload_text,
    ensure_wordlists_dir,
    list_wordlists,
    parse_and_validate_wordlist_text,
)
from word_retrieval.pages.confirm import render_confirm_page
from word_retrieval.pages.message import render_message_page
from word_retrieval.pages.result import render_result_page
from word_retrieval.pages.settings import render_settings_page
from word_retrieval.user_data import (
    apply_confirm_updates,
    dump_user_data,
    is_custom_wordlist,
    parse_user_data,
    resolve_known_words,
    client_dict_overrides,
)
from word_retrieval.vocab_doc import build_vocabulary_docx

bp = Blueprint("main", __name__)

_DOWNLOADS: dict[str, dict] = {}
_SESSIONS: dict[str, dict] = {}
_TOKEN_RE = re.compile(r"^[0-9a-f]{32}$")
_MAX_CACHE_AGE_SEC = 3600


def _cleanup_downloads() -> None:
    now = time.time()
    expired = [
        token
        for token, meta in _DOWNLOADS.items()
        if now - meta["created_at"] > _MAX_CACHE_AGE_SEC
    ]
    for token in expired:
        meta = _DOWNLOADS.pop(token, None)
        if meta is None:
            continue
        path = Path(meta["path"])
        if path.exists():
            path.unlink(missing_ok=True)


def _cleanup_sessions() -> None:
    now = time.time()
    expired = [
        sid
        for sid, meta in _SESSIONS.items()
        if now - meta["created_at"] > _MAX_CACHE_AGE_SEC
    ]
    for sid in expired:
        _SESSIONS.pop(sid, None)


def _safe_stem(filename: str) -> str:
    stem = Path(filename).stem
    stem = re.sub(r"[^\w\-]+", "_", stem, flags=re.UNICODE).strip("_")
    return stem or "document"


def _store_download(content: bytes, download_name: str) -> str:
    _cleanup_downloads()
    cache_dir = Path(current_app.config["DOWNLOAD_DIR"])
    cache_dir.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex
    output_path = cache_dir / f"{token}.docx"
    output_path.write_bytes(content)
    _DOWNLOADS[token] = {
        "path": str(output_path),
        "download_name": download_name,
        "created_at": time.time(),
    }
    return token


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
    return html.replace("<!--BASELINE_WORDLISTS_JSON-->", baseline_json)


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
    except Exception as exc:  # noqa: BLE001
        return render_message_page("对照表错误", str(exc), status=400)

    try:
        dictionary = _classification_dictionary(user_data)
    except EcdictError as exc:
        return render_message_page("缺少大词典", str(exc), status=500)

    words = extract_english_words(text)
    from word_retrieval.lexicon import classify_words

    green, yellow, red = classify_words(words, known=known, dictionary=dictionary)

    print("=" * 40)
    print(f"来源: {source_label}")
    print(f"对照表: {wordlist_name}（用户差分已合并）")
    print(f"总计 {len(words)} | 绿 {len(green)} | 黄 {len(yellow)} | 红 {len(red)}")
    print("=" * 40)

    _cleanup_sessions()
    session_id = uuid.uuid4().hex
    _SESSIONS[session_id] = {
        "created_at": time.time(),
        "source_label": source_label,
        "stem": stem,
        "highlight_bytes": highlight_bytes,
        "wordlist_name": wordlist_name,
        "user_data": user_data,
        "baseline_names": baseline,
        "green": green,
        "yellow": yellow,
        "red": red,
    }
    return render_confirm_page(
        session_id=session_id,
        source_label=source_label,
        wordlist_name=wordlist_name,
        green_words=green,
        yellow_words=yellow,
        red_words=red,
    )


def _finalize_session(
    session: dict,
    *,
    green_to_vocab: set[str],
    green_remove_words: set[str],
    yellow_to_words: set[str],
    yellow_to_dict: set[str],
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

    updated_user_data, saved_count, removed_count = apply_confirm_updates(
        user_data,
        wordlist_name=wordlist_name,
        baseline_names=baseline_names,
        green_remove_words=green_remove_words,
        yellow_to_words=yellow_to_words,
        yellow_to_dict=yellow_to_dict,
        red_to_words=red_to_words,
    )

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
    highlight_bytes = session.get("highlight_bytes")
    if highlight_bytes is not None:
        try:
            highlighted = build_highlighted_docx(
                highlight_bytes,
                green=doc_green,
                yellow=doc_yellow,
                red=doc_red,
            )
        except Exception as exc:  # noqa: BLE001
            return render_message_page("处理失败", f"文档着色出错：{exc}", status=500)
        highlight_name = f"{stem}_highlighted.docx"
        highlight_token = _store_download(highlighted, highlight_name)

    vocab_words = keep_red | green_to_vocab

    translate_error = None
    vocab_token = None
    vocab_name = f"{stem}_unknown_vocab.docx"
    try:
        sorted_vocab = sorted(vocab_words)
        definitions = lookup_definitions(
            sorted_vocab,
            Path(current_app.config["ECDICT_DB"]),
        )
        pairs = [
            (word, definitions.get(word, "") or "（词库未收录）") for word in sorted_vocab
        ]
        missing = sum(1 for _, text in pairs if text == "（词库未收录）")
        if missing and sorted_vocab:
            translate_error = (
                f"ECDICT 未命中 {missing}/{len(sorted_vocab)} 个词，"
                "已在释义表中标注「词库未收录」。"
            )
        vocab_token = _store_download(build_vocabulary_docx(pairs), vocab_name)
    except EcdictError as exc:
        translate_error = str(exc)
        pairs = [(word, "") for word in sorted(vocab_words)]
        vocab_token = _store_download(build_vocabulary_docx(pairs), vocab_name)
    except Exception as exc:  # noqa: BLE001
        translate_error = f"查词过程出错：{exc}"
        pairs = [(word, "") for word in sorted(vocab_words)]
        vocab_token = _store_download(build_vocabulary_docx(pairs), vocab_name)

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
    return render_settings_page(baseline_wordlists=names)


@bp.post("/api/parse_wordlist")
def api_parse_wordlist():
    """校验上传的对照表 txt，可选扩展屈折；结果由前端写入 localStorage。"""
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
        add_inflections = (request.form.get("add_inflections") or "") == "1"
        if add_inflections:
            words_set = expand_with_inflections(words)
        else:
            words_set = set(words)
        sorted_words = sorted(words_set)
        return jsonify(
            {
                "ok": True,
                "words": sorted_words,
                "base_count": base_count,
                "total_count": len(sorted_words),
                "with_inflections": add_inflections,
            }
        )
    except Exception as exc:  # noqa: BLE001
        return jsonify({"ok": False, "error": str(exc)}), 400


@bp.post("/upload")
def upload():
    uploaded = request.files.get("document")
    article = (request.form.get("article") or "").strip()
    has_file = uploaded is not None and bool(uploaded.filename)
    wordlist_name = (request.form.get("wordlist") or "words.txt").strip()
    user_data = parse_user_data(request.form.get("user_data"))

    if not has_file and not article:
        return render_message_page(
            "未收到内容",
            "请上传 Word 文档，或在文本框中输入文章后再提交。",
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
            doc_text = read_docx_text(file_bytes)
        except (BadZipFile, PackageNotFoundError, ValueError):
            return render_message_page(
                "无法读取文档",
                "文件不是有效的 .docx（也可能是旧版 .doc）。请用 Word/WPS 另存为 .docx 后再试。",
            )
        except Exception as exc:  # noqa: BLE001
            return render_message_page("处理失败", f"服务器处理出错：{exc}", status=500)

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
    _cleanup_sessions()
    session_id = (request.form.get("session_id") or "").strip()
    if not _TOKEN_RE.fullmatch(session_id):
        return render_message_page("会话无效", "请重新提交文章或文档。", status=400)

    session = _SESSIONS.pop(session_id, None)
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

    return _finalize_session(
        session,
        green_to_vocab=green_to_vocab,
        green_remove_words=green_remove_words,
        yellow_to_words=yellow_to_words,
        yellow_to_dict=yellow_to_dict,
        keep_red=keep_red,
        red_to_words=red_to_words,
    )


@bp.get("/download/<token>")
def download_file(token: str):
    if not _TOKEN_RE.fullmatch(token):
        return render_message_page("无效链接", "下载链接无效。", status=404)

    _cleanup_downloads()
    meta = _DOWNLOADS.get(token)
    if meta is None:
        return render_message_page(
            "文件已过期",
            "文档缓存已失效，请重新提交生成。",
            status=404,
        )

    path = Path(meta["path"])
    if not path.exists():
        _DOWNLOADS.pop(token, None)
        return render_message_page(
            "文件已过期",
            "文档不存在，请重新提交生成。",
            status=404,
        )

    return send_file(
        path,
        as_attachment=True,
        download_name=meta["download_name"],
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
