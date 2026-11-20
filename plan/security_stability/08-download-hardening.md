# SECURITY 2.4：下载硬化

## 范围

- **做（已实现）**
  - `GET /download/<token>` 只读 `.cache/downloads/{token}.docx`，忽略 meta JSON 里的 `path`。
  - `Content-Disposition` 文件名经 `safe_download_name` 白名单（basename、词干 `[^\w\-]`→`_`、后缀必须 `.docx`、词干长度帽约 80）；洗不出来则 `document.docx`。
  - 写入（`store_download`）与读出（`get_download`）各洗一次；路由对路径 `resolve()` 后确认仍在 `download_dir` 内。
- **已有、本项不改**
  - token `^[0-9a-f]{32}$`；首次下载后删除；TTL 约 30 分钟。
- **不做**
  - 账号绑定 / 签名 token；改 Nginx；改 CSRF；改确认页勾选默认。

## 现状锚点（改之前）

- `download_file` 用 `Path(meta["path"])`，`download_name` 原样交给 `send_file`。
- `get_download` 可读 meta.`path`；`store_download` 不洗文件名。
- 正常流程文件名来自 `_safe_stem`（`{stem}_highlighted.docx` / `{stem}_unknown_vocab.docx`）。

## 实现要点

- `job_cache.py`：`safe_download_name`；`store_download` / `get_download` 使用之；`path` 固定 `_download_docx_path(download_dir, token)`。
- `routes.py`：`download_file` 路径必须在 `download_dir` 内；`send_file` 用洗过的名；读入内存 → `delete_download` → 发送（不变）。

## 验收

- `../x.docx`、`a/b.docx`、带引号或换行的名字 → `document.docx` 或仅含词字符的 `*.docx`。
- 正常 `笔记_highlighted.docx` 保持可读。
- meta 里 `path` 指向目录外时，`get_download` 仍指向 `{token}.docx`。
- 合法 token 第二次请求仍是「已过期或已下载」。

## 落地记录

- 日期：2026-11-20
- 状态：已实现
