"""用户端差分数据：解析、与服务器基准合并、应用确认页改动。"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from word_retrieval.lexicon import (
    load_known_words,
    normalize_words,
    resolve_wordlist_path,
)

USER_DATA_VERSION = 1


def empty_user_data() -> dict[str, Any]:
    return {
        "version": USER_DATA_VERSION,
        "dict_extra": [],
        "dict_exclude": [],
        "patches": {},
        "custom_lists": {},
    }


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

    data["dict_extra"] = sorted(
        normalize_words(_as_str_list(parsed.get("dict_extra")))
    )
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

    return data


def dump_user_data(data: dict[str, Any]) -> str:
    payload = {
        "version": USER_DATA_VERSION,
        "dict_extra": sorted(normalize_words(data.get("dict_extra") or [])),
        "dict_exclude": sorted(normalize_words(data.get("dict_exclude") or [])),
        "patches": {},
        "custom_lists": {},
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
    extra = normalize_words(user_data.get("dict_extra") or [])
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


def dict_add_words(user_data: dict[str, Any], words: set[str]) -> int:
    to_add = normalize_words(words)
    if not to_add:
        return 0
    extra = set(user_data.get("dict_extra") or [])
    exclude = set(user_data.get("dict_exclude") or [])
    fresh = to_add - extra
    exclude -= to_add
    extra |= to_add
    user_data["dict_extra"] = sorted(extra)
    user_data["dict_exclude"] = sorted(exclude)
    return len(fresh)


def dict_exclude_words(user_data: dict[str, Any], words: set[str]) -> int:
    to_ex = normalize_words(words)
    if not to_ex:
        return 0
    extra = set(user_data.get("dict_extra") or [])
    exclude = set(user_data.get("dict_exclude") or [])
    extra -= to_ex
    fresh = to_ex - exclude
    exclude |= to_ex
    user_data["dict_extra"] = sorted(extra)
    user_data["dict_exclude"] = sorted(exclude)
    return len(fresh)


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
    red_to_words: set[str],
) -> tuple[dict[str, Any], int, int]:
    """
    确认页写回：只改 user_data 副本，不碰服务器文件。
    返回 (新数据, 写入对照表或词典的词数, 从对照表剔除数)。
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
    saved += dict_add_words(updated, yellow_to_dict)
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
