# Word Retrieval / Word 单词提取

中英双语说明 · Bilingual README (中文 / English)

本地 Flask 工具：从 `.docx` 或粘贴文本中提取英语单词，按「已掌握 / 疑似专有 / 未掌握」三色分类，人工确认后下载**着色 Word**与基于 **ECDICT** 的**释义生词表**。

A local Flask app that extracts English words from `.docx` files or pasted text, classifies them into known / proper-like / unknown, lets you confirm by hand, then downloads a **highlighted Word** document and an **ECDICT-based vocabulary sheet**.

仓库 / Repository: <https://github.com/likelin-9650/Word-Retrieval>

---

## 功能特性 · Features

| 中文 | English |
|------|---------|
| 上传 `.docx` 或输入文章 | Upload `.docx` or paste article text |
| 绿 / 黄 / 红三色分类 | Green / yellow / red classification |
| 确认页勾选入库与释义表 | Confirm page for wordlists & vocab export |
| 下载着色文档 | Download color-highlighted `.docx` |
| 本地 ECDICT 多行释义 | Offline ECDICT definitions (POS, senses) |
| 多对照表管理（设置页） | Multiple checklist wordlists (Settings) |
| 大词典 `scowl_words.txt` 可维护 | Maintainable SCOWL-style dictionary |

**三色含义 · Color meanings**

- **绿 Green**：已在对照表中（视为已掌握） / Already in your checklist (known)
- **黄 Yellow**：不在大词典中（多为专有名词、拼写变体等） / Not in the large dictionary (often proper nouns)
- **红 Red**：在大词典中但不在对照表（未掌握，可进释义表） / In dictionary but not in checklist (unknown; can go to vocab sheet)

---

## 环境要求 · Requirements

- Python **3.10+**（推荐 3.12 / 3.14）
- Windows / macOS / Linux
- 仅支持 **`.docx`**（旧版 `.doc` 请先另存为 `.docx`）

依赖见 `requirements.txt`：

- `flask`
- `python-docx`
- `lemminflect`
- `requests`
- `wordfreq`

---

## 快速开始 · Quick Start

### 1. 克隆 · Clone

```bash
git clone https://github.com/likelin-9650/Word-Retrieval.git
cd Word-Retrieval
```

### 2. 虚拟环境 · Virtual environment

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -U pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

> `.venv` **不要**提交到 Git。克隆后请本地自行创建。  
> Do **not** commit `.venv`. Create it locally after cloning.

### 3. 准备词典数据 · Prepare dictionaries

**对照表 Checklist**（已掌握词）在 `wordlists/`，默认 `wordlists/words.txt`（一行一词）。

**大词典 Large dictionary**：`scowl_words.txt`（用于区分黄/红）。若缺失：

```bash
python build_scowl_words.py
```

**ECDICT 本地释义库**（生词表用）：生成 `dictionaries/ecdict.db`（约数十 MB，首次需下载 CSV）：

```bash
python build_ecdict_db.py
```

> `dictionaries/*.db` 默认被 `.gitignore` 忽略；每位使用者需自行构建一次。  
> The SQLite DB is gitignored; each user should build it once.

### 4. 启动服务 · Run the server

```bash
python app.py
```

浏览器打开 / Open: <http://127.0.0.1:5000>

---

## 使用流程 · How to Use

1. **首页**：选择对照表 → 上传 `.docx` 和/或粘贴文章 → 提交。  
   **Home**: pick a wordlist → upload `.docx` and/or paste text → submit.

2. **确认页**：  
   - 绿：可选写入对照表  
   - 黄：可选写入对照表 / 大词典  
   - 红：默认勾选「进入释义表」；可选写入对照表  
   **Confirm**: adjust green/yellow/red actions, then continue.

3. **结果页**：下载  
   - 着色后的 Word（若上传了文档）  
   - 未掌握词释义表（ECDICT：音标、词性、中文义项等）  
   **Result**: download highlighted docx (if any) and the vocabulary sheet.

4. **设置 `/settings`**：增删对照表、批量编辑对照表或大词典。  
   **Settings**: create/delete wordlists; bulk add/remove words.

上传体积上限约 **16MB**。会话与下载缓存约 **1 小时**有效。

---

## 项目结构 · Project Structure

```text
Word-Retrieval/
├── app.py                 # 启动入口 · App entry
├── index.html             # 首页 · Home page
├── requirements.txt
├── build_scowl_words.py   # 生成 scowl_words.txt
├── build_ecdict_db.py     # 下载 ECDICT 并生成 ecdict.db
├── scowl_words.txt        # 大词典 · Large English word list
├── wordlists/             # 对照表目录 · Checklist wordlists
│   └── words.txt
├── dictionaries/          # ECDICT SQLite（本地生成）
│   └── .gitkeep
├── word_retrieval/        # Flask 应用包 · App package
│   ├── __init__.py        # create_app()
│   ├── routes.py          # 路由与主流程 · Routes
│   ├── extractor.py       # 单词提取 · Extraction
│   ├── lexicon.py         # 词表与三色分类 · Lexicon
│   ├── highlighter.py     # 文档着色 · Highlighting
│   ├── ecdict.py          # ECDICT 查词 · Dictionary lookup
│   ├── vocab_doc.py       # 生成释义 Word · Vocab docx
│   └── pages/             # HTML 页面渲染 · Page templates
└── .gitignore
```

---

## 常用命令 · Common Commands

| 目的 Purpose | 命令 Command |
|--------------|--------------|
| 安装依赖 Install deps | `pip install -r requirements.txt` |
| 生成大词典 Build SCOWL list | `python build_scowl_words.py` |
| 生成 ECDICT 库 Build ECDICT DB | `python build_ecdict_db.py` |
| 启动网页 Start web app | `python app.py` |

---

## 可选：百度翻译 · Optional Baidu Translate

网页默认使用 **本地 ECDICT**，不调用百度 API。

源码中（如 `word_retrieval/routes.py`、`__init__.py`）留有注释，说明可改造接入百度翻译。完整百度 CLI 方案仅保留在作者本地，**默认不随仓库分发**；如需可联系作者。

The web UI uses **offline ECDICT** by default. Comments in the code mark where a Baidu Translate API could be wired in. The standalone Baidu CLI is kept locally by the author and is **not** shipped in this repository by default.

---

## 故障排除 · Troubleshooting

| 问题 Issue | 处理 Fix |
|------------|----------|
| 缺少大词典 / Missing `scowl_words.txt` | 运行 `python build_scowl_words.py` |
| 释义表提示未找到 ECDICT | 运行 `python build_ecdict_db.py` |
| 无法读取文档 | 确认是 `.docx`，非旧版 `.doc` |
| PowerShell 无法激活 `.venv` | 执行策略限制；可直接用 `.\.venv\Scripts\python.exe app.py` |
| 推送 GitHub 因大文件失败 | 勿提交 `.venv`；本仓库已在 `.gitignore` 中忽略 |

---

## 许可与致谢 · License & Credits

- 单词分类与学习流程为本项目实现。  
- 英文词表可来源于 [SCOWL](http://wordlist.aspell.net/) / [wordfreq](https://github.com/rspeer/wordfreq)。  
- 英汉释义数据基于 [ECDICT](https://github.com/skywind3000/ECDICT)（请遵守其许可证）。

---

## 联系 · Contact

Issues / 反馈：请在 GitHub 仓库提交 Issue。  
Open an issue on the repository for questions or bug reports.
