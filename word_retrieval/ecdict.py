"""本地 ECDICT 查词（SQLite）。"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

try:
    from lemminflect import getLemma
except ImportError:  # pragma: no cover
    getLemma = None  # type: ignore[assignment]


class EcdictError(RuntimeError):
    """ECDICT 词典不可用或查询失败。"""


@dataclass(frozen=True)
class DictEntry:
    word: str
    phonetic: str = ""
    translation: str = ""
    definition: str = ""
    pos: str = ""
    exchange: str = ""
    matched_as: str = ""  # 实际命中的词形（可能是原形）

    def format_text(self, *, include_english: bool = False) -> str:
        """格式化为适合写入生词表的多行释义。"""
        lines: list[str] = []
        if self.matched_as and self.matched_as.lower() != self.word.lower():
            lines.append(f"（词形还原 → {self.matched_as}）")
        phonetic = (self.phonetic or "").strip()
        if phonetic:
            lines.append(phonetic if phonetic.startswith("/") else f"/{phonetic}/")
        pos = (self.pos or "").strip()
        if pos:
            lines.append(f"[{pos}]")
        lines.extend(_split_field(self.translation))
        if include_english:
            eng = _split_field(self.definition)
            if eng:
                lines.append("——")
                lines.extend(eng)
        return "\n".join(lines).strip()


def _split_field(raw: str) -> list[str]:
    text = (raw or "").replace("\\n", "\n")
    return [line.strip() for line in text.splitlines() if line.strip()]


def _lemma_candidates(word: str) -> list[str]:
    w = word.strip().lower()
    if not w or getLemma is None:
        return []
    out: list[str] = []
    seen = {w}
    for pos in ("NOUN", "VERB", "ADJ", "ADV"):
        try:
            lemmas = getLemma(w, upos=pos) or []
        except Exception:  # noqa: BLE001
            continue
        for lemma in lemmas:
            key = str(lemma).strip().lower()
            if key and key not in seen:
                seen.add(key)
                out.append(key)
    return out


class Ecdict:
    """只读查询本地 ECDICT SQLite。"""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise EcdictError(
                f"未找到 ECDICT 数据库：{self.db_path.name}。"
                f"请先运行 build_ecdict_db.py 生成。"
            )
        self._conn = sqlite3.connect(
            f"file:{self.db_path.as_posix()}?mode=ro",
            uri=True,
        )
        self._conn.row_factory = sqlite3.Row

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> Ecdict:
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def _fetch(self, word: str) -> DictEntry | None:
        row = self._conn.execute(
            """
            SELECT word, phonetic, definition, translation, pos, exchange
            FROM ecdict
            WHERE word = ? COLLATE NOCASE
            LIMIT 1
            """,
            (word.strip(),),
        ).fetchone()
        if row is None:
            return None
        return DictEntry(
            word=str(row["word"] or word),
            phonetic=str(row["phonetic"] or ""),
            definition=str(row["definition"] or ""),
            translation=str(row["translation"] or ""),
            pos=str(row["pos"] or ""),
            exchange=str(row["exchange"] or ""),
            matched_as=str(row["word"] or word),
        )

    def lookup(self, word: str) -> DictEntry | None:
        """查词；直接命中失败时尝试词形还原。"""
        key = word.strip()
        if not key:
            return None
        hit = self._fetch(key)
        if hit is not None:
            return DictEntry(
                word=key.lower(),
                phonetic=hit.phonetic,
                definition=hit.definition,
                translation=hit.translation,
                pos=hit.pos,
                exchange=hit.exchange,
                matched_as=hit.matched_as,
            )
        for lemma in _lemma_candidates(key):
            hit = self._fetch(lemma)
            if hit is not None:
                return DictEntry(
                    word=key.lower(),
                    phonetic=hit.phonetic,
                    definition=hit.definition,
                    translation=hit.translation,
                    pos=hit.pos,
                    exchange=hit.exchange,
                    matched_as=hit.matched_as,
                )
        return None

    def lookup_many(self, words: list[str]) -> dict[str, DictEntry | None]:
        return {w.strip().lower(): self.lookup(w) for w in words if w.strip()}


def lookup_definitions(
    words: list[str],
    db_path: Path,
    *,
    include_english: bool = False,
) -> dict[str, str]:
    """
    批量查词，返回 {小写词: 格式化释义}。
    未命中时值为空字符串。
    """
    if not words:
        return {}
    with Ecdict(db_path) as dic:
        result: dict[str, str] = {}
        for word in words:
            key = word.strip().lower()
            if not key or key in result:
                continue
            entry = dic.lookup(word)
            result[key] = (
                entry.format_text(include_english=include_english) if entry else ""
            )
        return result


@lru_cache(maxsize=2)
def load_ecdict_headwords(db_path: str) -> frozenset[str]:
    """读取 ECDICT 全部词头（小写），用于黄/红分类大词典。"""
    path = Path(db_path)
    if not path.exists():
        raise EcdictError(
            f"未找到 ECDICT 数据库：{path.name}。请先运行 build_ecdict_db.py 生成。"
        )
    conn = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    try:
        rows = conn.execute("SELECT word FROM ecdict").fetchall()
    finally:
        conn.close()
    return frozenset(
        str(row[0]).strip().lower()
        for row in rows
        if row and str(row[0]).strip()
    )


def clear_ecdict_headwords_cache() -> None:
    load_ecdict_headwords.cache_clear()
