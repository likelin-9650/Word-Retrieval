# SECURITY 3.4：缓存与多进程（A+B）

## 范围

- **做（已实现）**
  - **A（文档）**：多 gunicorn worker 时，`load_ecdict_headwords` / `load_word_set` 各进程各持一份内存缓存；改盘上 `wordlists/*.txt` 或 `ecdict.db` 后，**各 worker 下次加载**按文件 mtime 惰性刷新；大换词典库仍可 `systemctl restart` 利落重置。
  - **B（代码）**：缓存键为 **path + `st_mtime_ns`**；对外 `load_word_set(path)` / `load_ecdict_headwords(db_path)` 签名不变；`clear_word_cache` / `clear_ecdict_headwords_cache` 清内部 cache。
  - ECDICT 内部 cache **`maxsize=1`**，避免换库后短暂双份约 70MB 词头集。
- **不做**
  - 跨进程广播失效、共享内存词典。
  - 分类改为按需 SQLite（方案 C）。
  - 把 ECDICT 全量灌进对照表。

## 决策（用户确认）

1. 3.4 选 **A+B**（不做 C）。
2. 禁止把 ECDICT 灌进对照表。

## 现状锚点（改之前）

- `@lru_cache` 只按 path 字符串键；文件内容变了仍命中旧集合。
- `clear_*` 只清当前进程；网页主流程已不写服务器共享词表。

## 实现要点

```mermaid
flowchart LR
  call["load_star path"] --> stat["Path.stat mtime_ns"]
  stat --> key["lru_cache key path plus mtime"]
  key -->|hit| ret[cached frozenset]
  key -->|miss| read[read disk or SQLite]
  read --> ret
```

1. **`lexicon.py`**：`_load_word_set_cached(path, mtime_ns)`，`maxsize=32`；文件不存在哨兵 mtime `-1`，仍返回空集。
2. **`ecdict.py`**：`_load_ecdict_headwords_cached`，`maxsize=1`；文件不存在仍抛 `EcdictError`。

## 验收

- 改临时词表后再 `load_word_set` 含新词；未改文件时 cache hits 增加；`clear_word_cache` 后 `currsize==0`。

## 落地记录

- 日期：2026-11-20
- 状态：已实现（mtime 键 + 文档约定）
