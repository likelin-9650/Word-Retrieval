---
name: Cache mtime dep lock
overview: 落地 SECURITY 3.4（文档约定 + 按文件 mtime 自动失效进程内 lru_cache）与 3.5（以本机 venv 为准钉死 requirements，含传递依赖与 gunicorn），并同步本地/公开文档。
todos:
  - id: mtime-cache
    content: lexicon/ecdict：path+mtime 的 lru_cache；ecdict 内部 maxsize=1；clear_* 对齐
    status: completed
  - id: pin-requirements
    content: requirements.txt 本机 freeze 全量 == 钉死 + gunicorn==23.0.0；deploy.yml 只装 requirements
    status: completed
  - id: docs
    content: 11/12 方案、SECURITY、HANDOFF、README 中英、DEPLOY 一句、build_readme_docx
    status: completed
isProject: false
---

# 3.4 A+B + 3.5 依赖锁定

## 范围

**做**

- **3.4 A**：文档写清多 worker 各持一份 `lru_cache`、改盘上基准表/`ecdict.db` 后的行为。
- **3.4 B**：`load_word_set` / `load_ecdict_headwords` 按文件 **mtime** 自动失效；对外函数签名不变。
- **3.5**：`requirements.txt` 全部 `==` 钉死（本机 `pip freeze` 的直接+传递依赖）+ **gunicorn**；`deploy.yml` 改为只 `pip install -r requirements.txt`。
- 方案文档：`11-cache-mtime.md`、`12-dep-lock.md`；更新 `SECURITY_STABILITY.md` §3.4/§3.5；`HANDOFF.md`；`README.md` 中英；`build_readme_docx.py`。
- **禁止**：把 ECDICT 灌进对照表；不做 3.4 C；不做 3.3 测试套件。

**不做**

- 跨进程广播清缓存、共享内存词典、改分类语义、改确认页勾选。

## 已锁定决策

| 项 | 决定 |
|----|------|
| 3.4 | A+B |
| 3.5 形式 | 直接改 `requirements.txt` 为 `包==版本` |
| 钉包范围 | 本机 freeze 全量 + gunicorn |
| 版本来源 | 本机 `.venv`；gunicorn → **`gunicorn==23.0.0`** |
| 文档 | SECURITY / HANDOFF / README（+docx）；SECURITY 与 HANDOFF 不 git 提交 |

## 3.4 B 实现

1. `lexicon.py`：公有 `load_word_set` + 内部 `_load_word_set_cached(path, mtime_ns)`，`maxsize=32`。
2. `ecdict.py`：同上；内部 **`maxsize=1`**。
3. 调用方不改。

## 3.5 实现

1. 本机 freeze 写入 `requirements.txt` + `gunicorn==23.0.0`。
2. `deploy.yml` 只 `pip install -r requirements.txt`。
3. `DEPLOY.md` 注明版本以仓库文件为准。

## 验收

- 改词表后同进程再 load 得新内容；`clear_*` 可用。
- `requirements.txt` 无裸 `>=`；含 gunicorn；deploy 与文件一致。
