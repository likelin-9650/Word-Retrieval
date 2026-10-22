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

    def format_text(
        self,
        *,
        include_english: bool | None = None,
        vocab_output: dict[str, bool] | None = None,
    ) -> str:
        """
        格式化为适合写入生词表的多行释义。

        vocab_output 控制 phonetic / translation / definition / exchange；
        词形还原提示始终输出；永不输出独立 pos 行。
        include_english 为旧参数：仅在未传 vocab_output 时生效（True 等价于打开 definition）。
        """
        flags = {
            "phonetic": True,
            "translation": True,
            "definition": False,
            "exchange": False,
        }
        if isinstance(vocab_output, dict):
            for key in flags:
                if key in vocab_output:
                    flags[key] = bool(vocab_output[key])
        elif include_english is not None:
            flags["definition"] = bool(include_english)

        lines: list[str] = []
        if self.matched_as and self.matched_as.lower() != self.word.lower():
            lines.append(f"（词形还原 → {self.matched_as}）")
        if flags["phonetic"]:
            phonetic = (self.phonetic or "").strip()
            if phonetic:
                lines.append(
                    phonetic if phonetic.startswith("/") else f"/{phonetic}/"
                )
        if flags["exchange"]:
            exchange = (self.exchange or "").strip()
            if exchange:
                lines.append(f"（词形：{exchange}）")
        if flags["translation"]:
            lines.extend(_split_field(self.translation))
        if flags["definition"]:
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


def entry_from_client(raw: dict) -> DictEntry:
    """将本机增补词条转为 DictEntry（字段与 ECDICT 对齐）。"""
    word = str(raw.get("word") or "").strip().lower()
    return DictEntry(
        word=word,
        phonetic=str(raw.get("phonetic") or "").strip(),
        definition=str(raw.get("definition") or "").strip(),
        translation=str(raw.get("translation") or "").strip(),
        pos=str(raw.get("pos") or "").strip(),
        exchange=str(raw.get("exchange") or "").strip(),
        matched_as=word,
    )


def lookup_definitions(
    words: list[str],
    db_path: Path,
    *,
    include_english: bool = False,
    client_entries: dict[str, dict] | None = None,
    vocab_output: dict[str, bool] | None = None,
) -> dict[str, str | None]:
    """
    批量查词，返回 {小写词: 格式化释义}。
    未命中时值为 None（与「命中但输出开关全关导致空串」区分）。
    client_entries：本机 ECDICT 增补；若该词有非空中文释义则优先于服务器 ECDICT。
    vocab_output：释义表字段开关（与设置页一致）；未传时可用 include_english 兼容旧调用。
    """
    if not words:
        return {}
    flags = vocab_output
    if flags is None and include_english:
        flags = {
            "phonetic": True,
            "translation": True,
            "definition": True,
            "exchange": False,
        }
    overlay = {
        str(k).strip().lower(): v
        for k, v in (client_entries or {}).items()
        if str(k).strip() and isinstance(v, dict)
    }
    with Ecdict(db_path) as dic:
        result: dict[str, str | None] = {}
        for word in words:
            key = word.strip().lower()
            if not key or key in result:
                continue
            client = overlay.get(key)
            if client and str(client.get("translation") or "").strip():
                result[key] = entry_from_client(client).format_text(
                    vocab_output=flags
                )
                continue
            entry = dic.lookup(word)
            result[key] = (
                entry.format_text(vocab_output=flags) if entry else None
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


def load_exchange_map(db_path: Path, words: list[str] | set[str]) -> dict[str, str]:
    """
    批量读取词头对应的 exchange 字段。
    返回 {小写词头: exchange 原文}；未命中不出现在结果中。
    """
    path = Path(db_path)
    if not path.exists():
        raise EcdictError(
            f"未找到 ECDICT 数据库：{path.name}。请先运行 build_ecdict_db.py 生成。"
        )
    keys = sorted(
        {
            str(w).strip().lower()
            for w in words
            if str(w).strip()
        }
    )
    if not keys:
        return {}
    out: dict[str, str] = {}
    conn = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    try:
        chunk = 500
        for i in range(0, len(keys), chunk):
            part = keys[i : i + chunk]
            placeholders = ",".join("?" * len(part))
            rows = conn.execute(
                f"""
                SELECT lower(word), exchange FROM ecdict
                WHERE lower(word) IN ({placeholders})
                """,
                part,
            ).fetchall()
            for word, exchange in rows:
                key = str(word or "").strip().lower()
                if not key:
                    continue
                text = str(exchange or "").strip()
                if text:
                    out[key] = text
    finally:
        conn.close()
    return out


def clear_ecdict_headwords_cache() -> None:
    load_ecdict_headwords.cache_clear()
