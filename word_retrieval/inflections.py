"""屈折派生词：lemminflect 算法 + ECDICT exchange。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from lemminflect import getAllInflections
except ImportError:  # pragma: no cover
    getAllInflections = None  # type: ignore[assignment]


def _is_simple_token(token: str) -> bool:
    t = token.strip().lower()
    if not t or len(t) > 64:
        return False
    # 允许字母与内部撇号，如 don't / it's（屈折结果一般不含）
    return all(ch.isalpha() or ch == "'" for ch in t)


def parse_exchange_forms(exchange: str) -> set[str]:
    """
    解析 ECDICT exchange 字段为词形集合。
    格式如 s:apples/p:ran/d:run/i:running；取冒号后的词形。
    """
    out: set[str] = set()
    raw = (exchange or "").strip()
    if not raw:
        return out
    for part in raw.split("/"):
        piece = part.strip()
        if not piece:
            continue
        if ":" in piece:
            _tag, _, form = piece.partition(":")
            token = form.strip().lower()
        else:
            token = piece.lower()
        if _is_simple_token(token):
            out.add(token)
    return out


def inflections_for_word(word: str) -> set[str]:
    """返回单个词的 lemminflect 屈折形式集合（含原词小写）。"""
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
    """对词表中每个词扩展 lemminflect 屈折派生词，返回去重后的小写集合。"""
    expanded: set[str] = set()
    for word in words:
        expanded |= inflections_for_word(str(word))
    return expanded


def expand_wordlist_forms(
    words: set[str] | list[str],
    *,
    ecdict_db: Path | None = None,
    use_ecdict_exchange: bool = True,
    algo_mode: str = "none",
) -> dict[str, Any]:
    """
    扩展对照表派生词。

    - ECDICT exchange：全部采信（写入 accepted）
    - algo_mode:
        none — 不用算法
        all  — 算法结果全部采信
        pick — ECDICT 词头中已有的算法结果直接采信；
               其余（算法有、ECDICT 无）放入 algo_candidates 供用户勾选

    返回 dict：
      accepted, algo_candidates, base_count,
      ecdict_added, algo_trusted_count, needs_pick
    """
    base = {str(w).strip().lower() for w in words if str(w).strip()}
    mode = (algo_mode or "none").strip().lower()
    if mode not in {"none", "all", "pick"}:
        mode = "none"

    accepted: set[str] = set(base)
    algo_candidates: set[str] = set()
    ecdict_added = 0
    algo_trusted_count = 0

    headwords: frozenset[str] = frozenset()
    if ecdict_db is not None and (use_ecdict_exchange or mode == "pick"):
        from word_retrieval.ecdict import load_ecdict_headwords, load_exchange_map

        db_path = Path(ecdict_db)
        if use_ecdict_exchange:
            exchange_map = load_exchange_map(db_path, base)
            before = len(accepted)
            for _word, exchange in exchange_map.items():
                accepted |= parse_exchange_forms(exchange)
            ecdict_added = len(accepted) - before
        if mode == "pick":
            headwords = load_ecdict_headwords(str(db_path))

    if mode in {"all", "pick"}:
        algo = expand_with_inflections(base)
        if mode == "all":
            before = len(accepted)
            accepted |= algo
            algo_trusted_count = len(accepted) - before
        else:
            # 算法结果里已在 ECDICT 词头中的 → 采信；其余待勾选
            trusted_algo = {w for w in algo if w in headwords} - accepted
            accepted |= trusted_algo
            algo_trusted_count = len(trusted_algo)
            algo_candidates = algo - accepted

    return {
        "accepted": sorted(accepted),
        "algo_candidates": sorted(algo_candidates),
        "base_count": len(base),
        "ecdict_added": ecdict_added,
        "algo_trusted_count": algo_trusted_count,
        "algo_mode": mode,
        "use_ecdict_exchange": bool(use_ecdict_exchange),
        "needs_pick": mode == "pick" and bool(algo_candidates),
    }
