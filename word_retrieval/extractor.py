"""从 Word 文档中提取英语单词。"""

from __future__ import annotations

import io
import re
import zipfile
from collections.abc import Iterator

from docx import Document

# 字母词，或 1st/2nd 等序数缩写
ENGLISH_WORD_RE = re.compile(
    r"[A-Za-z]+(?:'[A-Za-z]+)?|\d+(?:st|nd|rd|th)",
    re.IGNORECASE,
)

# 有独立语义的单字母词（其余单字母如型号中的 V、o 不提取）
MEANINGFUL_SINGLE_LETTERS = frozenset({"a", "i"})

DEFAULT_MAX_DOCX_ENTRIES = 2_000
DEFAULT_MAX_DOCX_UNCOMPRESSED = 64 * 1024 * 1024  # 64 MB
DEFAULT_MAX_DOCX_RATIO = 100.0


def is_meaningful_english_token(token: str) -> bool:
    """判断是否为应提取/着色的英语词元。"""
    if not token:
        return False
    # 序数缩写始终保留
    if token[0].isdigit():
        return True
    if len(token) == 1:
        return token.lower() in MEANINGFUL_SINGLE_LETTERS
    return True


def iter_english_tokens(text: str) -> Iterator[re.Match[str]]:
    """迭代文本中有意义的英语词元匹配。"""
    for match in ENGLISH_WORD_RE.finditer(text):
        if is_meaningful_english_token(match.group(0)):
            yield match


def extract_english_words(text: str) -> set[str]:
    """从文本中提取英语单词（小写去重）。"""
    return {match.group(0).lower() for match in iter_english_tokens(text)}


def assert_docx_package(
    file_bytes: bytes,
    *,
    max_entries: int = DEFAULT_MAX_DOCX_ENTRIES,
    max_uncompressed: int = DEFAULT_MAX_DOCX_UNCOMPRESSED,
    max_ratio: float = DEFAULT_MAX_DOCX_RATIO,
) -> None:
    """
    打开 Document 前检查 zip 条目数、声明解压体积与压缩比。
    失败抛 ValueError（中文原因）；坏包抛 zipfile.BadZipFile。
    """
    if not file_bytes:
        raise ValueError("上传文件内容为空")

    with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
        infos = zf.infolist()
        if len(infos) > max_entries:
            raise ValueError(
                f"文档结构过于复杂（压缩包条目数超过上限 {max_entries}）。"
            )
        total_uncompressed = 0
        for info in infos:
            declared = int(info.file_size or 0)
            if declared < 0:
                raise ValueError("文档声明的解压体积无效。")
            if declared > max_uncompressed:
                raise ValueError(
                    f"文档声明的解压体积过大（单条目上限 "
                    f"{max_uncompressed // (1024 * 1024)} MB）。"
                )
            total_uncompressed += declared
            if total_uncompressed > max_uncompressed:
                raise ValueError(
                    f"文档声明的解压体积过大（合计上限 "
                    f"{max_uncompressed // (1024 * 1024)} MB）。"
                )
            compressed = int(info.compress_size or 0)
            if compressed > 0 and declared / compressed > max_ratio:
                raise ValueError(
                    f"文档压缩比异常（超过上限 {int(max_ratio)}:1），已拒绝解析。"
                )


def read_docx_text(
    file_bytes: bytes,
    *,
    max_entries: int = DEFAULT_MAX_DOCX_ENTRIES,
    max_uncompressed: int = DEFAULT_MAX_DOCX_UNCOMPRESSED,
    max_ratio: float = DEFAULT_MAX_DOCX_RATIO,
) -> str:
    """读取 .docx 中的全部段落与表格文本。"""
    assert_docx_package(
        file_bytes,
        max_entries=max_entries,
        max_uncompressed=max_uncompressed,
        max_ratio=max_ratio,
    )

    document = Document(io.BytesIO(file_bytes))
    parts: list[str] = []

    for paragraph in document.paragraphs:
        if paragraph.text.strip():
            parts.append(paragraph.text)

    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    parts.append(cell.text)

    return "\n".join(parts)
