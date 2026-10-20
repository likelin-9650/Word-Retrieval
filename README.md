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
| 服务器提供基准对照表；个人改动存本浏览器 | Server baselines; personal edits in the browser |
| 多份对照表；可上传 `.txt` 创建（存本机） | Multiple wordlists; create from `.txt` (browser-local) |
| 上传时可扩展屈折派生词（lemminflect） | Optional inflection expansion |
| 大词典 = ECDICT 词头 ∪ 本机增补词条 − 本机排除 | ECDICT ∪ browser entries − browser exclude |
| 本机数据导出 / 导入 / 清除 | Export / import / clear browser data |
| 页脚展示 ICP 与公安备案 | ICP + MPS (Gong’an) beian in footer |

---

## 备案信息 · Filings

| 类型 | 编号 | 链接 |
|------|------|------|
| 工信部 ICP | 蜀ICP备2026058519号 | https://beian.miit.gov.cn/ |
| 公安备案 | 川公网安备51070302110809号 | https://beian.mps.gov.cn/#/query/webSearch?code=51070302110809 |

公安备案图标：`word_retrieval/static/beian-mps.png`。  
动态页脚由 `word_retrieval/pages/__init__.py` 生成；首页 `index.html` 为静态页脚，**改号时两处同步**。

---

## 核心概念 · Core Concepts

### 数据存放：服务器基准 + 浏览器差分 · Server baseline + browser delta

| 存放位置 | 内容 | Location |
|----------|------|----------|
| **服务器** | ECDICT（`dictionaries/ecdict.db`）；基准对照表（`wordlists/*.txt`，如默认 `words.txt`） | Shared base dictionary & checklists |
| **本浏览器**（localStorage） | 对基准对照表的增删差分；自建对照表全文；大词典增补/排除 | Personal patches, custom lists, dict overrides |

网页分类时：

```text
生效对照表 = (服务器基准表 ∪ 本机新增) − 本机删除
生效大词典 = (ECDICT ∪ 本机增补) − 本机排除
```

确认页、设置页的写回**只更新本浏览器**，不会改服务器上的共享文件。换浏览器、清站点数据或无痕模式会丢失本机改动；请在设置页使用**导出 JSON**备份。

Server keeps ECDICT and baseline checklists. Your edits live in the browser only. Export JSON from Settings to back up.

### 对照表 · Checklist

表示你**已掌握**的词。

- **基准表**：服务器 `wordlists/`（默认 `words.txt`，一行一个单词）。首页下拉中无「（本机）」标记。  
- **本机差分**：在设置或确认页对基准表增删后，选项旁显示「（已改）」。  
- **自建表**：设置中新建或上传的表，仅存本浏览器，选项旁显示「（本机）」。服务器基准表（如 `words.txt`）不可删除；只能删除本机自建表。

首页若新建了对照表却看不到，**刷新页面**后再选。

### 大词典 · Classification dictionary

用于区分**黄词 / 红词**，词头来自服务器 **`dictionaries/ecdict.db`（ECDICT）**。

设置页与确认页的增补/排除写在**本浏览器**，不直接改 ECDICT，也不再依赖服务器上的 `dict_extra.txt` / `dict_exclude.txt` 作为网页用户数据。

本机增补存为与 ECDICT 对齐的**完整词条**（`word` / `phonetic` / `definition` / `translation` / `pos` / `exchange`）：**中文释义与词性必填**，音标、英文释义、词形变化可选。查释义时，本机有中文释义的词条优先于服务器 ECDICT。旧版仅词头的 `dict_extra` 字符串列表仍可导入（仅参与分类，无释义）。

Client dictionary add-ons are full ECDICT-style entries stored in the browser (**Chinese gloss and POS required**). Optional: phonetic, English definition, exchange. Client entries with a Chinese gloss override server ECDICT on lookup.

### 三色含义 · Colors

| 颜色 | 含义 | Meaning |
|------|------|---------|
| **绿** | 已在当前生效对照表中 | In the effective checklist |
| **黄** | 不在生效大词典（常为专有名词等） | Not in effective dictionary |
| **红** | 在大词典中，但不在对照表 | In dictionary, not in checklist |

### 确认页勾选 · Confirm-page actions

**绿色词**（已在对照表，两项默认不勾选）

- **进入释义表**：写入本次生成的释义表  
- **剔出对照表**：从本机对照表差分中删除该词（着色时按未掌握/红处理）

**黄色词**

- **对照表** / **大词典（本机增补）**：可单独或同时勾选；写入本浏览器  
- 勾选**大词典**时须填写**中文释义与词性**（音标、英文释义、词形变化可选），与 ECDICT 字段对齐  


**红色词**

- **进入释义表**（默认勾选）  
- **加入对照表**（默认不勾选；写入本浏览器）  

释义表内容 =「红词勾选进入释义表」∪「绿词勾选进入释义表」。

---

## 环境要求 · Requirements

- Python **3.10+**（推荐 3.12 / 3.14）
- Windows / macOS / Linux
- 文档格式仅 **`.docx`**（旧版 `.doc` 请先另存）
- 现代浏览器（需支持 localStorage）

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

1. **首页** `/`：选择对照表（含本机自建/已改）→ 粘贴文章和/或上传 `.docx` → 提交。  
2. **确认页**：按绿/黄/红勾选（见上文）；黄词勾「大词典」须填中文释义与词性；写回本浏览器。  
3. **结果页**：下载着色文档（若上传了 Word）与释义表；本机差分自动保存。  
4. **设置** `/settings`：  
   - 编辑本机词典覆盖（完整 ECDICT 词条）/ 对照表差分  
   - 新建**空**对照表（本机）  
   - **上传 `.txt`** 创建对照表（服务器仅校验，可选派生词；结果存本机）  
   - 删除本机自建对照表（基准 `words.txt` 等不可删）  
   - **导出 / 导入 / 清除**本机数据  

上传文档大小上限约 **16MB**；会话与下载缓存约 **1 小时**（释义表/着色文档会短暂缓存在服务器 `.cache/downloads/`，过期清理）。

### 上传对照表格式 · Wordlist `.txt` format

- 扩展名 `.txt`；编码 UTF-8（也支持 UTF-8 BOM / GBK）  
- **一行一个**英语单词；允许空行  
- 允许：纯字母词、撇号缩写（如 `don't`）、序数（如 `1st`）  
- 不要：中文句子、一行多词、二进制；大小 ≤ **5MB**  
- 可选：勾选「添加派生词」→ 用 lemminflect 扩展屈折形式后写入本机对照表  

---

## 项目结构 · Project Structure

```text
Word-Retrieval/
├── app.py                      # 启动入口
├── index.html                  # 首页（合并基准表 + 本机表）
├── requirements.txt
├── README.md
├── README.docx                 # 与 README 同步的 Word 版说明
├── build_readme_docx.py        # 由 README.md 生成 README.docx
├── LICENSE                     # Apache-2.0
├── NOTICE
├── build_ecdict_db.py          # 生成 dictionaries/ecdict.db
├── build_scowl_words.py        # （可选）旧 scowl 词表，网页分类已不使用
├── wordlists/                  # 服务器基准对照表
│   └── words.txt
├── dictionaries/               # ECDICT 库（多数被 gitignore）
│   └── .gitkeep
└── word_retrieval/             # Flask 应用包
    ├── __init__.py             # create_app()
    ├── routes.py               # 路由与主流程
    ├── user_data.py            # 浏览器差分：解析 / 与基准合并
    ├── extractor.py            # 提取单词
    ├── lexicon.py              # 对照表 / 分类 / 上传校验
    ├── inflections.py          # 屈折派生词
    ├── ecdict.py               # ECDICT 查词与词头
    ├── highlighter.py          # 文档着色
    ├── vocab_doc.py            # 生成释义 Word
    ├── static/
    │   ├── user_data.js        # localStorage 读写
    │   └── beian-mps.png       # 公安备案图标
    └── pages/                  # 确认 / 结果 / 设置等页面（页脚含 ICP + 公安备案）
```

生产部署：push 到 GitHub **任意分支**（含 `main` / `feature/*` 等）都会触发 Actions 自动部署到同一台服务器；也可在 Actions 页手动 Run workflow。注意实验分支也会覆盖线上。

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
| 本机改动消失 | 是否清过站点数据/换了浏览器；用设置页「导出」备份 |
| 设置页按钮无反应 | 硬刷新（Ctrl+F5）；确认 `/static/user_data.js` 可访问；勿对 script 内 JSON 使用 html.escape |
| 推了代码但网站未更新 | 看 Actions 是否跑通；任意分支 push 都会部署，失败时看 workflow 日志 |
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
