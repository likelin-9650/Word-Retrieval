---
name: 缓存 mtime 3.4
overview: 落地 SECURITY 3.4 A+B：文档约定多 worker 各持一份缓存；load_word_set / load_ecdict_headwords 按文件 mtime 自动失效。不做按需 SQLite 分类。
todos:
  - id: mtime-cache
    content: lexicon/ecdict：path+mtime 的 lru_cache；ecdict 内部 maxsize=1；clear_* 对齐
    status: completed
  - id: docs-34
    content: 11 方案、SECURITY §3.4、HANDOFF、README 中英相关句
    status: completed
isProject: false
---

# 3.4 缓存与多进程（A+B）

## 范围

- **A**：文档写清多 worker 各持一份 `lru_cache`；mtime 变后各 worker 下次加载惰性刷新；大换 `ecdict.db` 仍可建议 restart。
- **B**：`load_word_set` / `load_ecdict_headwords` 按 **path + mtime_ns** 缓存；对外签名不变。
- **不做**：跨进程广播清缓存；3.4 C（分类改按需查 SQLite）；把 ECDICT 灌进对照表。

## 实现

1. [`word_retrieval/lexicon.py`](../../word_retrieval/lexicon.py)：公有 `load_word_set` stat mtime；内部 `_load_word_set_cached(path, mtime_ns)` `maxsize=32`；`clear_word_cache` 清内部。
2. [`word_retrieval/ecdict.py`](../../word_retrieval/ecdict.py)：同上；内部 **`maxsize=1`** 避免换库后双份词头集；`clear_ecdict_headwords_cache` 清内部。

## 验收

- 改词表文件后同进程再 load 得新内容；未改文件命中 cache；`clear_*` 可用。
