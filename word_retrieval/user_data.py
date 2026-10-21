"""用户端差分数据：解析、与服务器基准合并、应用确认页改动。"""

from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

from word_retrieval.lexicon import (
    load_known_words,
    normalize_words,
    resolve_wordlist_path,
)

USER_DATA_VERSION = 2

# 与 ECDICT 词条字段对齐；新增时仅 translation（中文释义）必填，
# 词性请写在中文释义里（如「n. 苹果」）；pos 字段保留兼容，可为空。
DICT_ENTRY_FIELDS = (
    "word",
    "phonetic",
    "definition",
    "translation",
    "pos",
    "exchange",
)

HIGHLIGHT_KEYS = ("green", "yellow", "red")
DEFAULT_HIGHLIGHT: dict[str, dict[str, Any]] = {
    "green": {"enabled": True, "hex": "#1b8f3a"},
    "yellow": {"enabled": True, "hex": "#c4a000"},
    "red": {"enabled": True, "hex": "#c62828"},
}
_HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def default_highlight() -> dict[str, dict[str, Any]]:
    return deepcopy(DEFAULT_HIGHLIGHT)


def normalize_highlight(raw: Any) -> dict[str, dict[str, Any]]:
    """规范化着色偏好；非法项回退默认。"""
    out = default_highlight()
    if not isinstance(raw, dict):
        return out
    for key in HIGHLIGHT_KEYS:
        item = raw.get(key)
        if not isinstance(item, dict):
            continue
        enabled = item.get("enabled", out[key]["enabled"])
        if isinstance(enabled, bool):
            out[key]["enabled"] = enabled
        elif enabled in (0, 1, "0", "1", "true", "false", "True", "False"):
            out[key]["enabled"] = str(enabled).lower() in ("1", "true")
        hex_raw = str(item.get("hex") or "").strip()
        if _HEX_RE.fullmatch(hex_raw):
            out[key]["hex"] = hex_raw.lower()
    return out


def get_highlight(user_data: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not user_data:
        return default_highlight()
    return normalize_highlight(user_data.get("highlight"))


def empty_user_data() -> dict[str, Any]:
    return {
        "version": USER_DATA_VERSION,
        "dict_extra": [],
        "dict_exclude": [],
        "patches": {},
        "custom_lists": {},
        "highlight": default_highlight(),
    }


def empty_dict_entry(word: str = "") -> dict[str, str]:
    return {
        "word": (word or "").strip().lower(),
        "phonetic": "",
        "definition": "",
        "translation": "",
        "pos": "",
        "exchange": "",
    }


def normalize_dict_entry(
    raw: Any,
    *,
    require_gloss: bool = False,
) -> dict[str, str] | None:
    """
    规范化一条本机 ECDICT 增补词条。
    兼容旧版纯字符串词头；require_gloss=True 时仅要求中文释义非空
    （词性写在释义中，如「n. 苹果」）。
    """
    if isinstance(raw, str):
        word = raw.strip().lower()
        if not word:
            return None
        entry = empty_dict_entry(word)
        if require_gloss:
            raise ValueError(f"「{word}」加入大词典时必须填写中文释义。")
        return entry
    if not isinstance(raw, dict):
        return None
    word = str(raw.get("word") or "").strip().lower()
    if not word:
        return None
    entry = empty_dict_entry(word)
    for key in DICT_ENTRY_FIELDS:
        if key == "word":
            continue
        entry[key] = str(raw.get(key) or "").strip()
    if require_gloss:
        if not entry["translation"]:
            raise ValueError(
                f"「{word}」加入大词典时必须填写中文释义（请同时写上词性，如 n. 苹果）。"
            )
    return entry


def normalize_dict_extra(raw: Any) -> list[dict[str, str]]:
    """解析 dict_extra：支持旧版字符串列表与新版词条对象列表。"""
    if raw is None:
        return []
    items = raw if isinstance(raw, (list, tuple)) else [raw]
    by_word: dict[str, dict[str, str]] = {}
    for item in items:
        try:
            entry = normalize_dict_entry(item, require_gloss=False)
        except ValueError:
            continue
        if entry is None:
            continue
        by_word[entry["word"]] = entry
    return sorted(by_word.values(), key=lambda e: e["word"])


def dict_extra_headwords(dict_extra: Any) -> set[str]:
    return {e["word"] for e in normalize_dict_extra(dict_extra)}


def client_dict_entries_map(user_data: dict[str, Any]) -> dict[str, dict[str, str]]:
    """本机增补词条映射（小写词头 → 词条）。"""
    return {e["word"]: e for e in normalize_dict_extra(user_data.get("dict_extra"))}


def parse_user_data(raw: str | None) -> dict[str, Any]:
    """解析前端提交的 JSON；非法时返回空结构。"""
    data = empty_user_data()
    if not raw or not str(raw).strip():
        return data
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return data
    if not isinstance(parsed, dict):
        return data

    data["dict_extra"] = normalize_dict_extra(parsed.get("dict_extra"))
    data["dict_exclude"] = sorted(
        normalize_words(_as_str_list(parsed.get("dict_exclude")))
    )

    patches_in = parsed.get("patches") or {}
    if isinstance(patches_in, dict):
        for name, patch in patches_in.items():
            key = _safe_list_filename(str(name))
            if not key or not isinstance(patch, dict):
                continue
            add = sorted(normalize_words(_as_str_list(patch.get("add"))))
            remove = sorted(normalize_words(_as_str_list(patch.get("remove"))))
            # 同一词不应同时在 add/remove
            add_set, remove_set = set(add), set(remove)
            both = add_set & remove_set
            add_set -= both
            remove_set -= both
            if add_set or remove_set:
                data["patches"][key] = {
                    "add": sorted(add_set),
                    "remove": sorted(remove_set),
                }

    customs = parsed.get("custom_lists") or {}
    if isinstance(customs, dict):
        for name, words in customs.items():
            key = _safe_list_filename(str(name))
            if not key:
                continue
            data["custom_lists"][key] = sorted(
                normalize_words(_as_str_list(words))
            )

    data["highlight"] = normalize_highlight(parsed.get("highlight"))
    return data


def dump_user_data(data: dict[str, Any]) -> str:
    payload = {
        "version": USER_DATA_VERSION,
        "dict_extra": normalize_dict_extra(data.get("dict_extra")),
        "dict_exclude": sorted(normalize_words(data.get("dict_exclude") or [])),
        "patches": {},
        "custom_lists": {},
        "highlight": normalize_highlight(data.get("highlight")),
    }
    for name, patch in (data.get("patches") or {}).items():
        key = _safe_list_filename(str(name))
        if not key or not isinstance(patch, dict):
            continue
        add = sorted(normalize_words(patch.get("add") or []))
        remove = sorted(normalize_words(patch.get("remove") or []))
        if add or remove:
            payload["patches"][key] = {"add": add, "remove": remove}
    for name, words in (data.get("custom_lists") or {}).items():
        key = _safe_list_filename(str(name))
        if not key:
            continue
        payload["custom_lists"][key] = sorted(normalize_words(words or []))
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace(
        "<", "\\u003c"
    )


def list_effective_wordlists(
    baseline_names: list[str],
    user_data: dict[str, Any],
) -> list[str]:
    """基准表（服务器）在前，用户自建表在后。"""
    names: list[str] = []
    seen: set[str] = set()
    for name in baseline_names:
        if name not in seen:
            names.append(name)
            seen.add(name)
    for name in sorted((user_data.get("custom_lists") or {}).keys()):
        if name not in seen:
            names.append(name)
            seen.add(name)
    return names


def is_custom_wordlist(user_data: dict[str, Any], name: str) -> bool:
    key = _safe_list_filename(name)
    return bool(key) and key in (user_data.get("custom_lists") or {})


def resolve_known_words(
    user_data: dict[str, Any],
    wordlist_name: str,
    wordlists_dir: Path,
) -> frozenset[str]:
    """合并服务器基准对照表与用户差分 / 自建表。"""
    key = _safe_list_filename(wordlist_name) or "words.txt"
    customs = user_data.get("custom_lists") or {}
    if key in customs:
        return frozenset(normalize_words(customs[key]))

    path = resolve_wordlist_path(wordlists_dir, key)
    base = set(load_known_words(str(path)))
    patch = (user_data.get("patches") or {}).get(key) or {}
    add = normalize_words(patch.get("add") or [])
    remove = normalize_words(patch.get("remove") or [])
    return frozenset((base | add) - remove)


def client_dict_overrides(
    user_data: dict[str, Any],
) -> tuple[set[str], set[str]]:
    extra = dict_extra_headwords(user_data.get("dict_extra"))
    exclude = normalize_words(user_data.get("dict_exclude") or [])
    return extra, exclude


def wordlist_add(
    user_data: dict[str, Any],
    wordlist_name: str,
    words: set[str],
    *,
    baseline_names: set[str],
) -> int:
    """向对照表加入单词（写差分或自建表），返回新增数量。"""
    key = _safe_list_filename(wordlist_name)
    if not key:
        raise ValueError("非法对照表名称")
    to_add = normalize_words(words)
    if not to_add:
        return 0

    customs = user_data.setdefault("custom_lists", {})
    if key in customs:
        existing = set(customs[key])
        fresh = sorted(to_add - existing)
        if not fresh:
            return 0
        customs[key] = sorted(existing | to_add)
        return len(fresh)

    if key not in baseline_names and key != "words.txt":
        # 允许对未知名创建自建表
        customs[key] = sorted(to_add)
        return len(to_add)

    patches = user_data.setdefault("patches", {})
    patch = patches.setdefault(key, {"add": [], "remove": []})
    add_set = set(patch.get("add") or [])
    remove_set = set(patch.get("remove") or [])
    fresh = to_add - add_set
    # 若曾标记删除，加入时取消删除
    remove_set -= to_add
    add_set |= to_add
    patch["add"] = sorted(add_set)
    patch["remove"] = sorted(remove_set)
    return len(fresh)


def wordlist_remove(
    user_data: dict[str, Any],
    wordlist_name: str,
    words: set[str],
) -> int:
    key = _safe_list_filename(wordlist_name)
    if not key:
        raise ValueError("非法对照表名称")
    to_remove = normalize_words(words)
    if not to_remove:
        return 0

    customs = user_data.setdefault("custom_lists", {})
    if key in customs:
        existing = set(customs[key])
        hit = existing & to_remove
        if not hit:
            return 0
        customs[key] = sorted(existing - to_remove)
        return len(hit)

    patches = user_data.setdefault("patches", {})
    patch = patches.setdefault(key, {"add": [], "remove": []})
    add_set = set(patch.get("add") or [])
    remove_set = set(patch.get("remove") or [])
    # 从 add 里拿掉；其余记入 remove（相对基准）
    from_add = add_set & to_remove
    add_set -= to_remove
    newly = to_remove - from_add - remove_set
    remove_set |= to_remove
    patch["add"] = sorted(add_set)
    patch["remove"] = sorted(remove_set)
    return len(from_add) + len(newly)


def dict_add_entries(
    user_data: dict[str, Any],
    entries: list[dict[str, Any]] | list[Any],
    *,
    require_gloss: bool = True,
) -> int:
    """
    写入本机 ECDICT 增补词条（完整字段）；同词覆盖。
    新增时默认要求中文释义；并从 dict_exclude 反排除。
    """
    if not entries:
        return 0
    by_word = client_dict_entries_map(user_data)
    exclude = set(user_data.get("dict_exclude") or [])
    fresh = 0
    for raw in entries:
        entry = normalize_dict_entry(raw, require_gloss=require_gloss)
        if entry is None:
            continue
        word = entry["word"]
        if word not in by_word:
            fresh += 1
        by_word[word] = entry
        exclude.discard(word)
    user_data["dict_extra"] = sorted(by_word.values(), key=lambda e: e["word"])
    user_data["dict_exclude"] = sorted(exclude)
    return fresh


def dict_add_words(user_data: dict[str, Any], words: set[str]) -> int:
    """兼容旧调用：仅词头写入（无释义）；新流程请用 dict_add_entries。"""
    return dict_add_entries(
        user_data,
        [empty_dict_entry(w) for w in normalize_words(words)],
        require_gloss=False,
    )


def dict_exclude_words(user_data: dict[str, Any], words: set[str]) -> int:
    to_ex = normalize_words(words)
    if not to_ex:
        return 0
    by_word = client_dict_entries_map(user_data)
    exclude = set(user_data.get("dict_exclude") or [])
    removed_extra = 0
    for word in to_ex:
        if word in by_word:
            del by_word[word]
            removed_extra += 1
    fresh = to_ex - exclude
    exclude |= to_ex
    user_data["dict_extra"] = sorted(by_word.values(), key=lambda e: e["word"])
    user_data["dict_exclude"] = sorted(exclude)
    return len(fresh) + removed_extra


def create_custom_list(
    user_data: dict[str, Any],
    name: str,
    words: set[str] | None = None,
    *,
    baseline_names: set[str],
) -> str:
    from word_retrieval.lexicon import SAFE_LIST_NAME

    raw = (name or "").strip()
    if raw.lower().endswith(".txt"):
        raw = raw[:-4]
    if not SAFE_LIST_NAME.fullmatch(raw):
        raise ValueError("对照表名称仅允许中英文、数字、下划线和短横线，最长 64。")
    key = f"{raw}.txt"
    if key in baseline_names or key in (user_data.get("custom_lists") or {}):
        raise FileExistsError(f"对照表已存在：{key}")
    user_data.setdefault("custom_lists", {})[key] = sorted(
        normalize_words(words or set())
    )
    return key


def delete_custom_list(user_data: dict[str, Any], name: str) -> None:
    key = _safe_list_filename(name)
    if not key:
        raise ValueError("非法对照表名称")
    if key.lower() == "words.txt":
        raise ValueError("默认对照表 words.txt 不可删除。")
    customs = user_data.setdefault("custom_lists", {})
    if key not in customs:
        raise ValueError(
            f"只能删除本浏览器中自建的对照表；「{key}」是服务器基准表或未找到。"
        )
    del customs[key]
    # 顺带清掉同名差分（若有）
    (user_data.get("patches") or {}).pop(key, None)


def apply_confirm_updates(
    user_data: dict[str, Any],
    *,
    wordlist_name: str,
    baseline_names: set[str],
    green_remove_words: set[str],
    yellow_to_words: set[str],
    yellow_to_dict: set[str],
    yellow_dict_entries: list[dict[str, Any]] | None = None,
    red_to_words: set[str],
) -> tuple[dict[str, Any], int, int]:
    """
    确认页写回：只改 user_data 副本，不碰服务器文件。
    返回 (新数据, 写入对照表或词典的词数, 从对照表剔除数)。
    黄词进大词典须带完整词条（中文释义必填，词性写在释义里）。
    """
    updated = deepcopy(user_data)
    saved = 0
    saved += wordlist_add(
        updated,
        wordlist_name,
        yellow_to_words | red_to_words,
        baseline_names=baseline_names,
    )
    removed = wordlist_remove(updated, wordlist_name, green_remove_words)

    entries = list(yellow_dict_entries or [])
    if yellow_to_dict:
        provided = {
            str(e.get("word") or "").strip().lower()
            for e in entries
            if isinstance(e, dict)
        }
        missing = sorted(yellow_to_dict - provided)
        if missing:
            raise ValueError(
                "勾选「大词典」的黄词须同步提交词条（含中文释义）："
                + "、".join(missing[:8])
                + ("…" if len(missing) > 8 else "")
            )
        # 只保留本次勾选的词
        entries = [
            e
            for e in entries
            if isinstance(e, dict)
            and str(e.get("word") or "").strip().lower() in yellow_to_dict
        ]
        saved += dict_add_entries(updated, entries, require_gloss=True)
    return updated, saved, removed


def _as_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple, set)):
        return [str(v) for v in value]
    return []


def _safe_list_filename(name: str) -> str:
    raw = (name or "").strip()
    if not raw:
        return ""
    candidate = Path(raw).name
    if not candidate.lower().endswith(".txt"):
        candidate += ".txt"
    # 拒绝路径穿越残留
    if candidate != Path(candidate).name:
        return ""
    return candidate
