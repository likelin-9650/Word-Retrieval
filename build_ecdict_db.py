"""下载 ECDICT CSV 并生成本地 SQLite 数据库 dictionaries/ecdict.db。"""

from __future__ import annotations

import csv
import sqlite3
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CACHE_DIR = ROOT / ".cache"
DICT_DIR = ROOT / "dictionaries"
DB_PATH = DICT_DIR / "ecdict.db"
CSV_PATH = CACHE_DIR / "ecdict.csv"
CSV_URLS = [
    "https://ghfast.top/https://raw.githubusercontent.com/skywind3000/ECDICT/master/ecdict.csv",
    "https://gh.ddlc.top/https://raw.githubusercontent.com/skywind3000/ECDICT/master/ecdict.csv",
    "https://raw.githubusercontent.com/skywind3000/ECDICT/master/ecdict.csv",
    "https://github.com/skywind3000/ECDICT/raw/master/ecdict.csv",
]


def download_csv(dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    # 完整基础版约 20MB+；若本地已有足够大的文件则复用
    if dest.exists() and dest.stat().st_size > 15_000_000:
        print(f"已存在 CSV：{dest} ({dest.stat().st_size} bytes)")
        return dest
    last_error: Exception | None = None
    partial = dest.with_suffix(".csv.part")
    for url in CSV_URLS:
        print(f"下载 ECDICT CSV：{url}")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=180) as resp, partial.open("wb") as out:
                total = 0
                while True:
                    chunk = resp.read(1024 * 256)
                    if not chunk:
                        break
                    out.write(chunk)
                    total += len(chunk)
                    if total % (5 * 1024 * 1024) < 256 * 1024:
                        print(f"  已下载 {total} bytes…")
            if total < 5_000_000:
                raise RuntimeError(f"文件过小：{total} bytes")
            partial.replace(dest)
            print(f"已保存：{dest} ({dest.stat().st_size} bytes)")
            return dest
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            print(f"失败：{exc}")
    raise SystemExit(f"无法下载 ECDICT CSV：{last_error}")


def build_db(csv_path: Path, db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA journal_mode=OFF")
        conn.execute("PRAGMA synchronous=OFF")
        conn.execute(
            """
            CREATE TABLE ecdict (
                word TEXT NOT NULL,
                phonetic TEXT,
                definition TEXT,
                translation TEXT,
                pos TEXT,
                exchange TEXT
            )
            """
        )
        sql = (
            "INSERT INTO ecdict(word, phonetic, definition, translation, pos, exchange) "
            "VALUES (?, ?, ?, ?, ?, ?)"
        )
        batch: list[tuple[str, str, str, str, str, str]] = []
        count = 0
        # ECDICT CSV 字段可能含换行，需加大限制
        csv.field_size_limit(min(sys.maxsize, 10_000_000))
        with csv_path.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                word = (row.get("word") or "").strip()
                if not word:
                    continue
                batch.append(
                    (
                        word,
                        (row.get("phonetic") or "").strip(),
                        (row.get("definition") or "").strip(),
                        (row.get("translation") or "").strip(),
                        (row.get("pos") or "").strip(),
                        (row.get("exchange") or "").strip(),
                    )
                )
                if len(batch) >= 5000:
                    conn.executemany(sql, batch)
                    count += len(batch)
                    batch.clear()
                    if count % 100000 == 0:
                        print(f"已写入 {count} 条…")
            if batch:
                conn.executemany(sql, batch)
                count += len(batch)
        print(f"共写入 {count} 条，正在建索引…")
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_ecdict_word ON ecdict(word COLLATE NOCASE)"
        )
        conn.commit()
    finally:
        conn.close()
    print(f"完成：{db_path} ({db_path.stat().st_size} bytes)")


def main() -> int:
    csv_path = download_csv(CSV_PATH)
    build_db(csv_path, DB_PATH)
    # 冒烟测试
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT word, phonetic, translation FROM ecdict WHERE word = ? COLLATE NOCASE",
        ("abandon",),
    ).fetchone()
    conn.close()
    if not row:
        print("警告：冒烟查询 abandon 未命中", file=sys.stderr)
        return 1
    print(f"冒烟测试 OK：{row[0]} {row[1]} -> {str(row[2])[:80]}…")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
