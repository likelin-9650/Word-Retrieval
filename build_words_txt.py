"""从词汇表 JSON 生成含词形变化的 words.txt。"""

from __future__ import annotations

import json
import re
from pathlib import Path

from lemminflect import getInflection

ROOT = Path(__file__).resolve().parent
SOURCES = [
    ROOT / "vocab_pages_1_20.json",
    ROOT / "vocab_pages_21_40.json",
    ROOT / "output_41_61.json",
]
OUTPUT = ROOT / "words.txt"

INDEX_LETTER = re.compile(r"^[a-z]$")
MORE_MOST = re.compile(r"^(more|most)\b", re.I)
NON_WORD_CHARS = re.compile(r"[^a-z0-9'.\-/ ]+")
VOWEL_GROUPS = re.compile(r"[aeiouy]+", re.I)


def load_entries() -> list[dict]:
    entries: list[dict] = []
    for path in SOURCES:
        text = path.read_text(encoding="utf-8-sig")
        data = json.loads(text)
        if not isinstance(data, list):
            raise ValueError(f"{path.name} is not a JSON array")
        entries.extend(data)
        print(f"loaded {path.name}: {len(data)}")
    return entries


# 明确使用 -er/-est（或不规则）的常见形容词
FORCE_ER_EST = {
    "good",
    "bad",
    "well",
    "far",
    "old",
    "late",
    "little",
    "many",
    "much",
    "great",
    "high",
    "low",
    "hard",
    "near",
    "early",
    "happy",
    "heavy",
    "busy",
    "easy",
    "funny",
    "pretty",
    "ugly",
    "simple",
    "narrow",
    "clever",
    "gentle",
    "humble",
    "noble",
    "able",
}


def uses_er_est(adj: str) -> bool:
    """判断形容词是否用 -er/-est（否则应为 more/most，按需求直接跳过）。"""
    w = adj.lower()
    if w in FORCE_ER_EST:
        return True
    if "." in w or "-" in w or " " in w:
        return False
    # 以 y 结尾的较短形容词：happy → happier
    if w.endswith("y") and len(w) <= 8 and not w.endswith(("ly", "ay", "ey", "oy", "uy")):
        return True
    if w.endswith(("le", "er", "ow")) and len(w) <= 8:
        return True
    # 单音节/极短词：big, hot, tall
    groups = VOWEL_GROUPS.findall(w)
    if len(w) <= 5 and len(groups) <= 2:
        return True
    return False


def normalize_token(token: str) -> str | None:
    token = token.strip().lower()
    token = token.replace("’", "'").replace("‘", "'")
    # drop footnote marks / superscripts leftovers
    token = re.sub(r"[¹²³⁴⁵⁶⁷⁸⁹⁰]+", "", token)
    token = NON_WORD_CHARS.sub("", token)
    token = re.sub(r"\s+", " ", token).strip(" -")
    if not token:
        return None
    return token


def is_allowed_inflection(form: str) -> bool:
    form = form.strip().lower()
    if not form:
        return False
    if " " in form and MORE_MOST.match(form):
        return False
    if form.startswith("more ") or form.startswith("most "):
        return False
    return True


def inflect_word(word: str, pos_tags: set[str]) -> set[str]:
    forms: set[str] = {word}
    if " " in word:
        return forms

    lemma = word
    tags = {p.lower() for p in pos_tags}

    # 缩写不做词形变化
    if tags and tags <= {"abbr"}:
        return forms
    if "." in lemma:
        return forms

    if "n" in tags:
        for form in getInflection(lemma, tag="NNS") or ():
            if is_allowed_inflection(form):
                forms.add(form.lower())

    if "v" in tags:
        for tag in ("VBD", "VBG", "VBN"):
            for form in getInflection(lemma, tag=tag) or ():
                if is_allowed_inflection(form):
                    forms.add(form.lower())

    if "a" in tags and uses_er_est(lemma):
        for tag in ("JJR", "JJS"):
            for form in getInflection(lemma, tag=tag) or ():
                if is_allowed_inflection(form) and " " not in form:
                    forms.add(form.lower())

    return forms


def merge_by_word(entries: list[dict]) -> dict[str, set[str]]:
    """Map base token -> union of POS tags (for inflection)."""
    pos_map: dict[str, set[str]] = {}

    for entry in entries:
        tags = {str(p).lower() for p in (entry.get("pos") or [])}
        if "modal" in tags:
            tags.add("v")

        head = normalize_token(str(entry.get("word", "")))
        if head:
            # drop A/B/C... index headers that slipped through with empty POS
            if INDEX_LETTER.fullmatch(head) and not tags:
                continue
            pos_map.setdefault(head, set()).update(tags)

        for item in entry.get("variants", []) or []:
            v = normalize_token(str(item))
            if v:
                pos_map.setdefault(v, set()).update(tags)

        for item in entry.get("irregulars", []) or []:
            irr = normalize_token(str(item))
            if irr:
                pos_map.setdefault(irr, set())

    return pos_map


def main() -> None:
    entries = load_entries()
    pos_map = merge_by_word(entries)

    all_words: set[str] = set()
    for word, tags in pos_map.items():
        all_words.update(inflect_word(word, tags))

    cleaned = sorted(
        {
            w
            for w in all_words
            if w
            and not (INDEX_LETTER.fullmatch(w) and w not in {"a", "i"})
            and not w.startswith("more ")
            and not w.startswith("most ")
        }
    )

    OUTPUT.write_text("\n".join(cleaned) + "\n", encoding="utf-8")
    print(f"entries: {len(entries)}")
    print(f"unique head/variant tokens: {len(pos_map)}")
    print(f"wrote {len(cleaned)} lines -> {OUTPUT}")


if __name__ == "__main__":
    main()
