# Word Retrieval / Word 单词提取

中英双语说明 · Bilingual README (中文 / English)

本地 Flask 网页工具：从 `.docx` 或粘贴文本提取英语单词，按**绿 / 黄 / 红**三色分类，在确认页人工勾选后，下载**着色 Word**与基于 **ECDICT** 的**释义表**。

A local Flask web app that extracts English words from `.docx` or pasted text, classifies them **green / yellow / red**, lets you confirm actions by hand, then downloads a **highlighted Word** file and an **ECDICT-based vocabulary sheet**.

仓库 / Repository: <https://github.com/likelin-9650/Word-Retrieval>

---

## 功能概览 · Features

| 中文 | English |
|------|---------|
| 上传 `.docx` 或粘贴文章 | Upload `.docx` or paste text |
| 绿 / 黄 / 红三色分类 | Three-color classification |
| 确认页精细勾选（释义表 / 对照表 / 大词典） | Confirm-page checkboxes |
| 下载三色标注 Word | Download color-highlighted `.docx` |
| ECDICT 本地释义（音标、词性、义项） | Offline ECDICT definitions |
| 多份对照表；可上传 `.txt` 创建 | Multiple wordlists; create from `.txt` |
| 上传时可扩展屈折派生词（lemminflect） | Optional inflection expansion |
| 大词典 = ECDICT 词头 + 本地增补/排除 | ECDICT + local override files |

---

## 核心概念 · Core Concepts

### 对照表 · Checklist（`wordlists/*.txt`）

表示你**已掌握**的词。默认文件：`wordlists/words.txt`（一行一个单词）。

首页若新建了对照表却看不到，**刷新页面**后再选。

### 大词典 · Classification dictionary

用于区分**黄词 / 红词**，词头来自本地 **`dictionaries/ecdict.db`（ECDICT）**。

设置页可维护本地覆盖（不直接改 ECDICT 库）：

- `dictionaries/dict_extra.txt` — 增补词  
- `dictionaries/dict_exclude.txt` — 排除词  

### 三色含义 · Colors

| 颜色 | 含义 | Meaning |
|------|------|---------|
| **绿** | 已在当前对照表中 | In the selected checklist |
| **黄** | 不在 ECDICT 大词典（常为专有名词等） | Not in ECDICT |
| **红** | 在 ECDICT 中，但不在对照表 | In ECDICT, not in checklist |

### 确认页勾选 · Confirm-page actions

**绿色词**（已在对照表，两项默认不勾选）

- **进入释义表**：写入本次生成的释义表  
- **剔出对照表**：从当前对照表文件中删除该词（着色时按未掌握/红处理）

**黄色词**

- **对照表** / **大词典（ECDICT 增补）**：可单独或同时勾选  

**红色词**

- **进入释义表**（默认勾选）  
- **加入对照表**（默认不勾选）  

释义表内容 =「红词勾选进入释义表」∪「绿词勾选进入释义表」。

---

## 环境要求 · Requirements

- Python **3.10+**（推荐 3.12 / 3.14）
- Windows / macOS / Linux
- 文档格式仅 **`.docx`**（旧版 `.doc` 请先另存）

依赖（见 `requirements.txt`）：`flask`、`python-docx`、`lemminflect`、`requests`、`wordfreq`

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

> 不要把 `.venv` 提交到 Git。 / Do **not** commit `.venv`.

### 3. 生成 ECDICT 数据库 · Build ECDICT DB

分类与释义都依赖 `dictionaries/ecdict.db`（首次会下载 CSV，体积较大）：

```bash
python build_ecdict_db.py
```

> `dictionaries/*.db` 已被 `.gitignore` 忽略，每位使用者需自行生成一次。

### 4. 启动 · Run

```bash
python app.py
```

浏览器打开 / Open: <http://127.0.0.1:5000>

---

## 使用流程 · Workflow

1. **首页** `/`：选择对照表 → 粘贴文章和/或上传 `.docx` → 提交。  
2. **确认页**：按绿/黄/红勾选（见上文）。  
3. **结果页**：下载着色文档（若上传了 Word）与释义表。  
4. **设置** `/settings`：  
   - 编辑对照表 / 大词典覆盖  
   - 新建**空**对照表  
   - **上传 `.txt`** 创建对照表（可勾选添加派生词）  
   - 删除对照表（默认 `words.txt` 不可删）

上传文档大小上限约 **16MB**；会话与下载缓存约 **1 小时**。

### 上传对照表格式 · Wordlist `.txt` format

- 扩展名 `.txt`；编码 UTF-8（也支持 UTF-8 BOM / GBK）  
- **一行一个**英语单词；允许空行  
- 允许：纯字母词、撇号缩写（如 `don't`）、序数（如 `1st`）  
- 不要：中文句子、一行多词、二进制；大小 ≤ **5MB**  
- 可选：勾选「添加派生词」→ 用 lemminflect 扩展屈折形式后写入

---

## 项目结构 · Project Structure

```text
Word-Retrieval/
├── app.py                      # 启动入口
├── index.html                  # 首页
├── requirements.txt
├── README.md
├── LICENSE                     # Apache-2.0
├── NOTICE
├── build_ecdict_db.py          # 生成 dictionaries/ecdict.db
├── build_scowl_words.py        # （可选）旧 scowl 词表，网页分类已不使用
├── wordlists/                  # 对照表
│   └── words.txt
├── dictionaries/               # ECDICT 库与本地覆盖（多数被 gitignore）
│   └── .gitkeep
└── word_retrieval/             # Flask 应用包
    ├── __init__.py             # create_app()
    ├── routes.py               # 路由与主流程
    ├── extractor.py            # 提取单词
    ├── lexicon.py              # 对照表 / 分类 / 上传校验
    ├── inflections.py          # 屈折派生词
    ├── ecdict.py               # ECDICT 查词与词头
    ├── highlighter.py          # 文档着色
    ├── vocab_doc.py            # 生成释义 Word
    └── pages/                  # 确认 / 结果 / 设置等页面
```

---

## 常用命令 · Commands

| 目的 | 命令 |
|------|------|
| 安装依赖 | `pip install -r requirements.txt` |
| 生成 ECDICT | `python build_ecdict_db.py` |
| 启动服务 | `python app.py` |

---

## 可选：百度翻译 · Optional Baidu Translate

网页主流程使用 **本地 ECDICT** 生成释义，不调用百度 API。

源码（如 `routes.py`、`__init__.py`）中留有改造注释。百度独立 CLI 默认**不随仓库分发**；如需可联系作者。

---

## 故障排除 · Troubleshooting

| 问题 | 处理 |
|------|------|
| 分类/释义提示缺少 ECDICT | 运行 `python build_ecdict_db.py` |
| 上传对照表被拒 | 检查一行一词、编码、扩展名 `.txt` |
| 新对照表首页不显示 | 刷新网页 |
| 无法读取文档 | 使用 `.docx`，非旧版 `.doc` |
| PowerShell 无法 `Activate.ps1` | 直接用 `.\.venv\Scripts\python.exe app.py` |
| GitHub 推送因大文件失败 | 勿提交 `.venv` |

---

## 许可与致谢 · License & Credits

本项目代码采用 **Apache License 2.0**，见 [`LICENSE`](LICENSE) 与 [`NOTICE`](NOTICE)。  
Source code: **Apache License 2.0**.

Copyright © 2026 likelin

- 学习流程与网页实现为本项目原创。  
- 英汉释义数据基于 [ECDICT](https://github.com/skywind3000/ECDICT)（请遵守其自身许可）。  
- 可选旧词表脚本可能用到 [SCOWL](http://wordlist.aspell.net/) / [wordfreq](https://github.com/rspeer/wordfreq)。  
- 第三方数据许可独立于本仓库的 Apache-2.0 代码许可。

---

## 联系 · Contact

问题与建议请在 GitHub 仓库提交 Issue。  
Please open an Issue on the repository.
