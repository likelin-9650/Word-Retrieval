"""用 lemminflect 生成英语屈折派生词。"""

from __future__ import annotations

try:
    from lemminflect import getAllInflections
except ImportError:  # pragma: no cover
    getAllInflections = None  # type: ignore[assignment]

# 仅保留由字母构成的屈折形式（过滤标点/空串）


def _is_simple_token(token: str) -> bool:
    t = token.strip().lower()
    if not t or len(t) > 64:
        return False
    # 允许字母与内部撇号，如 don't / it's（屈折结果一般不含）
    return all(ch.isalpha() or ch == "'" for ch in t)


def inflections_for_word(word: str) -> set[str]:
    """返回单个词的屈折形式集合（含原词小写）。"""
    base = word.strip().lower()
    if not base:
        return set()
    out: set[str] = {base}
    if getAllInflections is None:
        return out
    try:
        forms = getAllInflections(base) or {}
    except Exception:  # noqa: BLE001
        return out
    for _tag, variants in forms.items():
        for item in variants or ():
            token = str(item).strip().lower()
            if _is_simple_token(token):
                out.add(token)
    return out


def expand_with_inflections(words: set[str] | list[str]) -> set[str]:
    """对词表中每个词扩展屈折派生词，返回去重后的小写集合。"""
    expanded: set[str] = set()
    for word in words:
        expanded |= inflections_for_word(str(word))
    return expanded
