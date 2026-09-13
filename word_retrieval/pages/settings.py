"""设置页面：编辑大词典/对照表，新建对照表（空表或上传）。"""

from __future__ import annotations

import html

from flask import url_for


def render_settings_page(
    *,
    wordlists: list[str],
    selected_list: str,
    message: str = "",
    error: str = "",
) -> str:
    home = url_for("main.index")
    action = url_for("main.settings")
    options = "\n".join(
        f'<option value="{html.escape(name)}"'
        f'{" selected" if name == selected_list else ""}>'
        f"{html.escape(name)}</option>"
        for name in wordlists
    )
    msg_html = f'<p class="ok">{html.escape(message)}</p>' if message else ""
    err_html = f'<p class="error">{html.escape(error)}</p>' if error else ""

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>设置</title>
  <style>
    :root {{
      --bg-top: #e8f0f4;
      --bg-bottom: #f7f3ec;
      --ink: #1c2a32;
      --muted: #5a6b75;
      --accent: #0f6a5c;
      --accent-hover: #0b5449;
      --line: #c5d2da;
      --surface: rgba(255, 255, 255, 0.72);
      --danger: #c62828;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0; min-height: 100vh;
      font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at 12% 18%, rgba(15, 106, 92, 0.12), transparent 42%),
        linear-gradient(165deg, var(--bg-top), var(--bg-bottom));
      padding: 2rem 1rem 3rem;
    }}
    main {{ width: min(760px, 100%); margin: 0 auto; }}
    h1 {{ margin: 0 0 0.4rem; }}
    h2 {{ margin: 0 0 0.7rem; font-size: 1.05rem; }}
    .meta {{ color: var(--muted); margin: 0 0 1rem; line-height: 1.5; }}
    a {{ color: var(--accent); font-weight: 600; text-decoration: none; }}
    .panel {{
      background: var(--surface); border: 1px solid var(--line);
      padding: 1.1rem 1.2rem; margin-bottom: 1rem;
    }}
    label {{ display: block; font-weight: 600; margin: 0.5rem 0 0.35rem; }}
    input[type="text"], input[type="file"], select, textarea {{
      width: 100%; padding: 0.7rem; border: 1px solid var(--line);
      font: inherit; background: #fff;
    }}
    input[type="file"] {{ border-style: dashed; }}
    textarea {{ min-height: 110px; resize: vertical; }}
    .hint {{ color: var(--muted); font-size: 0.88rem; margin: 0.35rem 0 0.7rem; line-height: 1.45; }}
    .req {{
      background: rgba(28, 77, 110, 0.06); border: 1px solid var(--line);
      padding: 0.75rem 0.9rem; margin: 0.5rem 0 0.9rem; font-size: 0.88rem;
      color: var(--muted); line-height: 1.5;
    }}
    .req strong {{ color: var(--ink); }}
    .row {{ display: flex; flex-wrap: wrap; gap: 0.6rem; margin-top: 0.7rem; align-items: center; }}
    .check {{
      display: flex; align-items: center; gap: 0.45rem; font-weight: 600; margin: 0.6rem 0;
    }}
    .check input {{ width: auto; }}
    button, .btn {{
      appearance: none; border: 0; background: var(--accent); color: #fff;
      font: inherit; font-weight: 600; padding: 0.7rem 1rem; cursor: pointer;
    }}
    button:hover {{ background: var(--accent-hover); }}
    button.danger {{ background: var(--danger); }}
    .ok {{ color: var(--accent); }}
    .error {{ color: var(--danger); }}
  </style>
</head>
<body>
  <main>
    <h1>设置</h1>
    <p class="meta">
      大词典用于区分黄词/红词，词头来自本地 ECDICT，可在下方增补或排除。
      对照表表示「已掌握」词汇（绿色）。
    </p>
    <p class="meta"><a href="{home}">← 返回首页</a></p>
    {msg_html}
    {err_html}

    <section class="panel">
      <h2>编辑大词典（ECDICT + 本地覆盖）</h2>
      <p class="hint">
        基础词表为 ECDICT 全部词头。此处「添加」写入本地增补表，
        「删除」写入本地排除表（不直接改 ECDICT 数据库）。
      </p>
      <form method="post" action="{action}">
        <input type="hidden" name="action" value="edit_dict" />
        <label for="dict_add">添加单词（每行一个）</label>
        <textarea id="dict_add" name="add_words" placeholder="apple&#10;banana"></textarea>
        <label for="dict_remove">排除单词（每行一个）</label>
        <textarea id="dict_remove" name="remove_words" placeholder="obsoleteword"></textarea>
        <div class="row"><button type="submit">更新大词典覆盖</button></div>
      </form>
    </section>

    <section class="panel">
      <h2>编辑对照表</h2>
      <form method="post" action="{action}">
        <input type="hidden" name="action" value="edit_wordlist" />
        <label for="wordlist">选择对照表</label>
        <select id="wordlist" name="wordlist">{options}</select>
        <label for="list_add">添加单词（每行一个）</label>
        <textarea id="list_add" name="add_words"></textarea>
        <label for="list_remove">删除单词（每行一个）</label>
        <textarea id="list_remove" name="remove_words"></textarea>
        <div class="row"><button type="submit">更新对照表</button></div>
      </form>
    </section>

    <section class="panel">
      <h2>新建空对照表</h2>
      <form method="post" action="{action}">
        <input type="hidden" name="action" value="create_wordlist" />
        <label for="new_list">名称</label>
        <input id="new_list" name="new_name" type="text" placeholder="例如 cet4 或 考研词汇" required />
        <p class="hint">将保存为 wordlists/名称.txt（空文件，之后可再编辑）。</p>
        <div class="row"><button type="submit">创建空对照表</button></div>
      </form>
    </section>

    <section class="panel">
      <h2>上传 .txt 创建对照表</h2>
      <div class="req">
        <strong>文件格式与排版要求：</strong><br />
        1. 扩展名必须为 <strong>.txt</strong>；编码推荐 <strong>UTF-8</strong>（也支持带 BOM 的 UTF-8、GBK）。<br />
        2. <strong>一行一个英语单词</strong>；允许空行；不要用逗号/空格分隔多个词。<br />
        3. 单词仅为英文字母，或带撇号缩写（如 <code>don't</code>），或序数缩写（如 <code>1st</code>/<code>2nd</code>）。<br />
        4. 不要包含中文、标点句子、表格或二进制内容；文件大小不超过 <strong>5 MB</strong>。<br />
        5. 服务器会校验格式；非法行过多将拒绝导入。
      </div>
      <form method="post" action="{action}" enctype="multipart/form-data">
        <input type="hidden" name="action" value="upload_wordlist" />
        <label for="upload_name">对照表名称</label>
        <input id="upload_name" name="new_name" type="text" placeholder="例如 my_vocab" required />
        <label for="wordlist_file">选择 .txt 文件</label>
        <input id="wordlist_file" name="wordlist_file" type="file" accept=".txt,text/plain" required />
        <label class="check">
          <input type="checkbox" name="add_inflections" value="1" />
          添加所有上传单词的派生词（屈折变化：如动词过去式/分词、名词复数、形容词比较级等）
        </label>
        <p class="hint">勾选后将用 lemminflect 自动扩展词形，并与原词一并写入对照表（自动去重）。</p>
        <div class="row"><button type="submit">上传并创建</button></div>
      </form>
    </section>

    <section class="panel">
      <h2>删除对照表</h2>
      <form method="post" action="{action}" onsubmit="return confirm('确定删除该对照表？');">
        <input type="hidden" name="action" value="delete_wordlist" />
        <label for="del_list">选择对照表</label>
        <select id="del_list" name="wordlist">{options}</select>
        <p class="hint">默认 words.txt 不可删除。</p>
        <div class="row"><button class="danger" type="submit">删除对照表</button></div>
      </form>
    </section>
  </main>
</body>
</html>
"""
