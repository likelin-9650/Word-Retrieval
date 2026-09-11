"""生成本地大型英文词表 scowl_words.txt。

优先尝试下载 SCOWL；失败时回退到 wordfreq 的 large 英文词表
（体量与中大型 SCOWL 接近，并含大量词形）。
"""

from __future__ import annotations

import io
import re
import tarfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "scowl_words.txt"
URLS = [
    "https://github.com/en-wl/wordlist/archive/refs/tags/scowl-2020.12.07.tar.gz",
    "https://downloads.sourceforge.net/project/wordlist/SCOWL/2020.12.07/scowl-2020.12.07.tar.gz",
]
NAME_RE = re.compile(r"(?:^|/)english-words\.(\d+)$")


def build_from_scowl() -> set[str] | None:
    data = None
    for url in URLS:
        try:
            print(f"downloading SCOWL: {url}")
            with urllib.request.urlopen(url, timeout=60) as resp:
                data = resp.read()
            print(f"downloaded {len(data)} bytes")
            break
        except Exception as exc:  # noqa: BLE001
            print(f"failed: {exc}")
    if not data:
        return None

    words: set[str] = set()
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tf:
        for member in tf.getmembers():
            name = member.name.replace("\\", "/")
            match = NAME_RE.search(name)
            if not match or int(match.group(1)) > 70:
                continue
            handle = tf.extractfile(member)
            if handle is None:
                continue
            for line in handle.read().decode("utf-8", errors="ignore").splitlines():
                word = line.strip().lower()
                if word and (word.isalpha() or "'" in word):
                    words.add(word)
    return words


def build_from_wordfreq() -> set[str]:
    from wordfreq import iter_wordlist

    print("fallback: building from wordfreq large list")
    return {
        w.lower()
        for w in iter_wordlist("en", wordlist="large")
        if w.isalpha() or "'" in w
    }


def main() -> None:
    words = build_from_scowl()
    source = "SCOWL<=70"
    if not words:
        words = build_from_wordfreq()
        source = "wordfreq-large"
    OUT.write_text("\n".join(sorted(words)) + "\n", encoding="utf-8")
    print(f"wrote {OUT} source={source} count={len(words)} bytes={OUT.stat().st_size}")


if __name__ == "__main__":
    main()
