"""本地词库、大词典与对照表管理。"""

from __future__ import annotations

import re
import shutil
from functools import lru_cache
from pathlib import Path

ORDINAL_RE = re.compile(r"^\d+(?:st|nd|rd|th)$", re.IGNORECASE)
SAFE_LIST_NAME = re.compile(r"^[A-Za-z0-9_\-\u4e00-\u9fff]{1,64}$")


@lru_cache(maxsize=32)
def load_word_set(path: str) -> frozenset[str]:
    """读取一行一词的词表，返回小写集合。"""
    file_path = Path(path)
    if not file_path.exists():
        return frozenset()
    text = file_path.read_text(encoding="utf-8")
    return frozenset(line.strip().lower() for line in text.splitlines() if line.strip())


def clear_word_cache() -> None:
    load_word_set.cache_clear()


def load_known_words(path: str) -> frozenset[str]:
    """读取对照表（如 words.txt）。"""
    return load_word_set(path)


def load_dictionary(path: str) -> frozenset[str]:
    """读取本地大词典。"""
    return load_word_set(path)


def is_in_dictionary(word: str, dictionary: frozenset[str]) -> bool:
    """是否视为词典内合法英语词（序数缩写视为合法）。"""
    w = word.lower()
    if ORDINAL_RE.fullmatch(w):
        return True
    return w in dictionary


def classify_words(
    words: set[str],
    *,
    known: frozenset[str],
    dictionary: frozenset[str],
) -> tuple[set[str], set[str], set[str]]:
    """
    三色分类：
    - green: 已在对照表
    - yellow: 不在大词典（疑似专有名词等）
    - red: 在大词典中，但不在对照表
    """
    green: set[str] = set()
    yellow: set[str] = set()
    red: set[str] = set()
    for word in words:
        w = word.lower()
        if w in known:
            green.add(w)
        elif not is_in_dictionary(w, dictionary):
            yellow.add(w)
        else:
            red.add(w)
    return green, yellow, red


def normalize_words(words: set[str] | list[str]) -> set[str]:
    return {w.lower().strip() for w in words if str(w).strip()}


def append_words_to_file(path: Path, words: set[str]) -> int:
    """将新词追加到词表文件，返回新增数量。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    existing: set[str] = set()
    text = ""
    if path.exists():
        text = path.read_text(encoding="utf-8")
        existing = {line.strip().lower() for line in text.splitlines() if line.strip()}

    to_add = sorted(normalize_words(words) - existing)
    if not to_add:
        return 0

    prefix = ""
    if text and not text.endswith("\n"):
        prefix = "\n"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(prefix + "\n".join(to_add) + "\n")
    clear_word_cache()
    return len(to_add)


def remove_words_from_file(path: Path, words: set[str]) -> int:
    """从词表删除单词，返回删除数量。"""
    if not path.exists():
        return 0
    remove_set = normalize_words(words)
    if not remove_set:
        return 0

    lines = path.read_text(encoding="utf-8").splitlines()
    kept: list[str] = []
    removed = 0
    for line in lines:
        word = line.strip().lower()
        if not word:
            continue
        if word in remove_set:
            removed += 1
            continue
        kept.append(word)
    if removed:
        path.write_text(("\n".join(sorted(set(kept))) + "\n") if kept else "", encoding="utf-8")
        clear_word_cache()
    return removed


def ensure_wordlists_dir(wordlists_dir: Path, legacy_words: Path | None = None) -> Path:
    """确保对照表目录存在，并初始化默认 words.txt。"""
    wordlists_dir.mkdir(parents=True, exist_ok=True)
    default_path = wordlists_dir / "words.txt"
    if not default_path.exists():
        if legacy_words and legacy_words.exists():
            shutil.copy2(legacy_words, default_path)
        else:
            default_path.write_text("", encoding="utf-8")
    return default_path


def list_wordlists(wordlists_dir: Path) -> list[str]:
    """返回对照表文件名（不含路径），按名称排序，words.txt 优先。"""
    ensure_wordlists_dir(wordlists_dir)
    names = sorted(p.name for p in wordlists_dir.glob("*.txt") if p.is_file())
    if "words.txt" in names:
        names.remove("words.txt")
        names.insert(0, "words.txt")
    return names


def resolve_wordlist_path(wordlists_dir: Path, name: str | None) -> Path:
    """解析用户选择的对照表路径，防止路径穿越。"""
    ensure_wordlists_dir(wordlists_dir)
    raw = (name or "words.txt").strip() or "words.txt"
    candidate = Path(raw).name
    if not candidate.lower().endswith(".txt"):
        candidate += ".txt"
    path = (wordlists_dir / candidate).resolve()
    if wordlists_dir.resolve() not in path.parents and path != wordlists_dir.resolve():
        raise ValueError("非法对照表路径")
    if not path.exists():
        raise FileNotFoundError(f"对照表不存在：{candidate}")
    return path


def create_wordlist(wordlists_dir: Path, name: str) -> Path:
    """新建对照表（不可用于大词典）。"""
    ensure_wordlists_dir(wordlists_dir)
    raw = name.strip()
    if raw.lower().endswith(".txt"):
        raw = raw[:-4]
    if not SAFE_LIST_NAME.fullmatch(raw):
        raise ValueError("对照表名称仅允许中英文、数字、下划线和短横线，最长 64。")
    path = wordlists_dir / f"{raw}.txt"
    if path.exists():
        raise FileExistsError(f"对照表已存在：{path.name}")
    path.write_text("", encoding="utf-8")
    clear_word_cache()
    return path


def delete_wordlist(wordlists_dir: Path, name: str) -> None:
    """删除对照表（不允许删除默认 words.txt）。"""
    path = resolve_wordlist_path(wordlists_dir, name)
    if path.name.lower() == "words.txt":
        raise ValueError("默认对照表 words.txt 不可删除。")
    path.unlink()
    clear_word_cache()
