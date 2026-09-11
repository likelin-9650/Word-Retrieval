"""HTTP 路由。"""

from __future__ import annotations

import re
import time
import uuid
from pathlib import Path
from zipfile import BadZipFile

from docx.opc.exceptions import PackageNotFoundError
from flask import Blueprint, current_app, request, send_file

from word_retrieval.ecdict import EcdictError, lookup_definitions
from word_retrieval.extractor import extract_english_words, read_docx_text
from word_retrieval.highlighter import build_highlighted_docx
from word_retrieval.lexicon import (
    append_words_to_file,
    classify_words,
    create_wordlist,
    delete_wordlist,
    ensure_wordlists_dir,
    list_wordlists,
    load_dictionary,
    load_known_words,
    normalize_words,
    remove_words_from_file,
    resolve_wordlist_path,
)
from word_retrieval.pages.confirm import render_confirm_page
from word_retrieval.pages.message import render_message_page
from word_retrieval.pages.result import render_result_page
from word_retrieval.pages.settings import render_settings_page
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


def _parse_words_textarea(raw: str) -> set[str]:
    return normalize_words(raw.replace(",", "\n").splitlines())


def _wordlists_dir() -> Path:
    return Path(current_app.config["WORDLISTS_DIR"])


def _render_index(selected_wordlist: str = "words.txt") -> str:
    html = Path(current_app.config["INDEX_HTML"]).read_text(encoding="utf-8")
    names = list_wordlists(_wordlists_dir())
    options = []
    for name in names:
        selected = " selected" if name == selected_wordlist else ""
        options.append(f'<option value="{name}"{selected}>{name}</option>')
    options_html = "\n          ".join(options)
    return html.replace("<!--WORDLIST_OPTIONS-->", options_html)


def _begin_review(
    text: str,
    *,
    source_label: str,
    wordlist_path: Path,
    highlight_bytes: bytes | None = None,
    stem: str = "article",
):
    dict_path = Path(current_app.config["SCOWL_WORDS"])
    if not dict_path.exists():
        return render_message_page(
            "缺少大词典",
            f"未找到 {dict_path.name}。请运行 build_scowl_words.py 生成。",
            status=500,
        )
    if not wordlist_path.exists():
        return render_message_page(
            "缺少对照表",
            f"未找到对照表：{wordlist_path.name}",
            status=500,
        )

    known = load_known_words(str(wordlist_path))
    dictionary = load_dictionary(str(dict_path))
    words = extract_english_words(text)
    green, yellow, red = classify_words(words, known=known, dictionary=dictionary)

    print("=" * 40)
    print(f"来源: {source_label}")
    print(f"对照表: {wordlist_path.name}")
    print(f"总计 {len(words)} | 绿 {len(green)} | 黄 {len(yellow)} | 红 {len(red)}")
    print("=" * 40)

    _cleanup_sessions()
    session_id = uuid.uuid4().hex
    _SESSIONS[session_id] = {
        "created_at": time.time(),
        "source_label": source_label,
        "stem": stem,
        "highlight_bytes": highlight_bytes,
        "wordlist_path": str(wordlist_path),
        "wordlist_name": wordlist_path.name,
        "green": green,
        "yellow": yellow,
        "red": red,
    }
    return render_confirm_page(
        session_id=session_id,
        source_label=source_label,
        wordlist_name=wordlist_path.name,
        green_words=green,
        yellow_words=yellow,
        red_words=red,
    )


def _finalize_session(
    session: dict,
    *,
    save_green: set[str],
    yellow_to_words: set[str],
    yellow_to_dict: set[str],
    keep_red: set[str],
    red_to_words: set[str],
):
    words_path = Path(session["wordlist_path"])
    dict_path = Path(current_app.config["SCOWL_WORDS"])

    save_green &= set(session["green"])
    yellow_to_words &= set(session["yellow"])
    yellow_to_dict &= set(session["yellow"])
    keep_red &= set(session["red"])
    red_to_words &= set(session["red"])

    saved_to_words = append_words_to_file(
        words_path,
        save_green | yellow_to_words | red_to_words,
    )
    saved_to_dict = append_words_to_file(dict_path, yellow_to_dict)

    # 文档着色：按用户操作后的最终归属
    doc_green = set(session["green"]) | save_green | yellow_to_words | red_to_words
    doc_yellow = set(session["yellow"]) - yellow_to_dict - yellow_to_words
    # 加入大词典但未进对照表的黄词，按红处理（普通未掌握）
    moved_to_dict_only = yellow_to_dict - yellow_to_words - doc_green
    doc_red = (keep_red | moved_to_dict_only) - doc_green
    # 未进入翻译表且未入库的原红词：不再标红（保持默认色）——仍可在结果中体现为未保留
    # 文档里对“不翻译也不入库”的红词保持红色提示？用户说不保存则不进入翻译表；着色上仍可标红表示未掌握。
    # 更合理：文档中所有未掌握的红词仍标红，无论是否进入翻译表；仅翻译表用 keep_red。
    doc_red = (set(session["red"]) | moved_to_dict_only) - doc_green
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

    # 生词释义：当前使用本地 ECDICT。
    # 此处可以改造接入百度翻译 API：将下方 lookup_definitions 替换为
    #   from word_retrieval.baidu_translate import BaiduTranslateError, translate_words
    #   translations = translate_words(sorted_red, Path(current_app.config["BAIDU_SECRETS"]))
    #   pairs = [(word, translations.get(word, "")) for word in sorted_red]
    translate_error = None
    vocab_token = None
    vocab_name = f"{stem}_unknown_vocab.docx"
    try:
        sorted_red = sorted(keep_red)
        definitions = lookup_definitions(
            sorted_red,
            Path(current_app.config["ECDICT_DB"]),
        )
        pairs = [(word, definitions.get(word, "") or "（词库未收录）") for word in sorted_red]
        missing = sum(1 for _, text in pairs if text == "（词库未收录）")
        if missing and sorted_red:
            translate_error = (
                f"ECDICT 未命中 {missing}/{len(sorted_red)} 个词，"
                "已在释义表中标注「词库未收录」。"
            )
        vocab_token = _store_download(build_vocabulary_docx(pairs), vocab_name)
    except EcdictError as exc:
        translate_error = str(exc)
        pairs = [(word, "") for word in sorted(keep_red)]
        vocab_token = _store_download(build_vocabulary_docx(pairs), vocab_name)
    except Exception as exc:  # noqa: BLE001
        translate_error = f"查词过程出错：{exc}"
        pairs = [(word, "") for word in sorted(keep_red)]
        vocab_token = _store_download(build_vocabulary_docx(pairs), vocab_name)

    # 结果页展示：按最终写入后的分类，红列表仅展示确认进入翻译表的词
    known = load_known_words(str(words_path))
    dictionary = load_dictionary(str(dict_path))
    all_words = set(session["green"]) | set(session["yellow"]) | set(session["red"])
    green, yellow, _red = classify_words(all_words, known=known, dictionary=dictionary)

    return render_result_page(
        source_label=f"{source_label}（对照表 {session['wordlist_name']}）",
        green_words=green,
        yellow_words=yellow,
        red_words=keep_red,
        highlight_token=highlight_token,
        highlight_name=highlight_name,
        vocab_token=vocab_token,
        vocab_name=vocab_name,
        translate_error=translate_error,
        saved_count=saved_to_words + saved_to_dict,
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
    names = list_wordlists(_wordlists_dir())
    return render_settings_page(wordlists=names, selected_list="words.txt")


@bp.post("/settings")
def settings_post():
    wordlists_dir = _wordlists_dir()
    ensure_wordlists_dir(
        wordlists_dir,
        legacy_words=Path(current_app.config["LEGACY_WORDS_TXT"]),
    )
    action = (request.form.get("action") or "").strip()
    message = ""
    error = ""
    selected = (request.form.get("wordlist") or "words.txt").strip() or "words.txt"

    try:
        if action == "edit_dict":
            dict_path = Path(current_app.config["SCOWL_WORDS"])
            added = append_words_to_file(
                dict_path, _parse_words_textarea(request.form.get("add_words") or "")
            )
            removed = remove_words_from_file(
                dict_path, _parse_words_textarea(request.form.get("remove_words") or "")
            )
            message = f"大词典已更新：新增 {added} 个，删除 {removed} 个。"

        elif action == "edit_wordlist":
            path = resolve_wordlist_path(wordlists_dir, selected)
            added = append_words_to_file(
                path, _parse_words_textarea(request.form.get("add_words") or "")
            )
            removed = remove_words_from_file(
                path, _parse_words_textarea(request.form.get("remove_words") or "")
            )
            message = f"对照表 {path.name} 已更新：新增 {added} 个，删除 {removed} 个。"
            selected = path.name

        elif action == "create_wordlist":
            path = create_wordlist(wordlists_dir, request.form.get("new_name") or "")
            message = f"已创建对照表：{path.name}"
            selected = path.name

        elif action == "delete_wordlist":
            delete_wordlist(wordlists_dir, selected)
            message = f"已删除对照表：{selected}"
            selected = "words.txt"

        else:
            error = "未知操作。"
    except Exception as exc:  # noqa: BLE001
        error = str(exc)

    names = list_wordlists(wordlists_dir)
    if selected not in names and names:
        selected = names[0]
    return render_settings_page(
        wordlists=names,
        selected_list=selected,
        message=message,
        error=error,
    )


@bp.post("/upload")
def upload():
    uploaded = request.files.get("document")
    article = (request.form.get("article") or "").strip()
    has_file = uploaded is not None and bool(uploaded.filename)
    wordlist_name = (request.form.get("wordlist") or "words.txt").strip()

    if not has_file and not article:
        return render_message_page(
            "未收到内容",
            "请上传 Word 文档，或在文本框中输入文章后再提交。",
        )

    try:
        wordlist_path = resolve_wordlist_path(_wordlists_dir(), wordlist_name)
    except Exception as exc:  # noqa: BLE001
        return render_message_page("对照表错误", str(exc), status=400)

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
            wordlist_path=wordlist_path,
            highlight_bytes=file_bytes,
            stem=_safe_stem(filename),
        )

    return _begin_review(
        article,
        source_label="文本输入",
        wordlist_path=wordlist_path,
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

    save_green = {
        v.strip().lower() for v in request.form.getlist("save_green") if v.strip()
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
        save_green=save_green,
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
