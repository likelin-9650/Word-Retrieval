"""本地词库、大词典与对照表管理。"""

from __future__ import annotations

import re
import shutil
from functools import lru_cache
from pathlib import Path

ORDINAL_RE = re.compile(r"^\d+(?:st|nd|rd|th)$", re.IGNORECASE)
SAFE_LIST_NAME = re.compile(r"^[A-Za-z0-9_\-\u4e00-\u9fff]{1,64}$")
# 上传对照表允许的词形：纯字母词、带撇号缩写、序数缩写
UPLOAD_WORD_RE = re.compile(
    r"^[A-Za-z]+(?:'[A-Za-z]+)?$|^\d+(?:st|nd|rd|th)$",
    re.IGNORECASE,
)
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_UPLOAD_WORDS = 200_000


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
    """读取本地大词典文本文件。"""
    return load_word_set(path)


def load_classification_dictionary(
    *,
    ecdict_db: Path,
    extra_path: Path | None = None,
    exclude_path: Path | None = None,
) -> frozenset[str]:
    """
    黄/红分类用大词典：ECDICT 全部词头 ∪ 本地增补 − 本地排除。
    """
    from word_retrieval.ecdict import load_ecdict_headwords

    base = set(load_ecdict_headwords(str(ecdict_db)))
    if extra_path is not None and extra_path.exists():
        base |= set(load_word_set(str(extra_path)))
    if exclude_path is not None and exclude_path.exists():
        base -= set(load_word_set(str(exclude_path)))
    return frozenset(base)


def ensure_dict_override_files(extra_path: Path, exclude_path: Path) -> None:
    extra_path.parent.mkdir(parents=True, exist_ok=True)
    if not extra_path.exists():
        extra_path.write_text("", encoding="utf-8")
    if not exclude_path.exists():
        exclude_path.write_text("", encoding="utf-8")


def update_dict_overrides(
    *,
    extra_path: Path,
    exclude_path: Path,
    add_words: set[str],
    remove_words: set[str],
) -> tuple[int, int]:
    """
    更新大词典本地覆盖层。
    新增写入 extra，并从 exclude 去掉；删除写入 exclude，并从 extra 去掉。
    返回 (写入增补数, 写入排除数)。
    """
    ensure_dict_override_files(extra_path, exclude_path)
    add_set = normalize_words(add_words)
    remove_set = normalize_words(remove_words)
    added = append_words_to_file(extra_path, add_set)
    if add_set:
        remove_words_from_file(exclude_path, add_set)
    if remove_set:
        remove_words_from_file(extra_path, remove_set)
        excluded = append_words_to_file(exclude_path, remove_set)
    else:
        excluded = 0
    return added, excluded


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


def create_wordlist(
    wordlists_dir: Path,
    name: str,
    *,
    words: set[str] | None = None,
) -> Path:
    """新建对照表；words 为空则创建空文件。"""
    ensure_wordlists_dir(wordlists_dir)
    raw = name.strip()
    if raw.lower().endswith(".txt"):
        raw = raw[:-4]
    if not SAFE_LIST_NAME.fullmatch(raw):
        raise ValueError("对照表名称仅允许中英文、数字、下划线和短横线，最长 64。")
    path = wordlists_dir / f"{raw}.txt"
    if path.exists():
        raise FileExistsError(f"对照表已存在：{path.name}")
    normalized = sorted(normalize_words(words or set()))
    path.write_text(
        ("\n".join(normalized) + "\n") if normalized else "",
        encoding="utf-8",
    )
    clear_word_cache()
    return path


def decode_upload_text(raw: bytes) -> str:
    """解码上传文本，优先 UTF-8，回退 UTF-8-SIG / GBK。"""
    if not raw:
        raise ValueError("上传文件为空。")
    if len(raw) > MAX_UPLOAD_BYTES:
        raise ValueError(f"文件过大，上限 {MAX_UPLOAD_BYTES // (1024 * 1024)} MB。")
    # 粗略拒绝明显二进制
    if b"\x00" in raw[:8192]:
        raise ValueError("文件疑似二进制，请上传纯文本 .txt。")
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("无法解码文件，请使用 UTF-8 或 GBK 编码的 .txt。")


def parse_and_validate_wordlist_text(text: str) -> list[str]:
    """
    校验对照表文本格式。
    要求：一行一个英语单词（可空行）；非法行过多则失败。
    返回去重后的小写词列表（排序）。
    """
    lines = text.splitlines()
    if not lines and not text.strip():
        raise ValueError("文件没有有效内容。")

    valid: set[str] = set()
    invalid_samples: list[str] = []
    invalid_count = 0
    non_empty = 0

    for line in lines:
        raw = line.strip()
        if not raw:
            continue
        # 允许行尾注释？用户要求严格一行一词，不支持注释
        non_empty += 1
        if UPLOAD_WORD_RE.fullmatch(raw):
            valid.add(raw.lower())
        else:
            invalid_count += 1
            if len(invalid_samples) < 5:
                invalid_samples.append(raw[:40])

    if non_empty == 0:
        raise ValueError("文件没有有效单词行（请一行一个英语单词）。")
    if len(valid) > MAX_UPLOAD_WORDS:
        raise ValueError(f"单词数量超过上限 {MAX_UPLOAD_WORDS}。")

    if invalid_count:
        sample = "、".join(invalid_samples) if invalid_samples else ""
        raise ValueError(
            f"格式不符合要求：共 {non_empty} 行非空，其中 {invalid_count} 行非法。"
            f"要求一行一个英语单词（字母词或 1st/2nd 等序数），请勿在同一行放多个词或中文。"
            + (f" 示例非法行：{sample}" if sample else "")
        )
    if not valid:
        raise ValueError("未解析到任何合法英语单词。")
    return sorted(valid)


def delete_wordlist(wordlists_dir: Path, name: str) -> None:
    """删除对照表（不允许删除默认 words.txt）。"""
    path = resolve_wordlist_path(wordlists_dir, name)
    if path.name.lower() == "words.txt":
        raise ValueError("默认对照表 words.txt 不可删除。")
    path.unlink()
    clear_word_cache()
