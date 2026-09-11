"""设置页面：编辑大词典/对照表，新建对照表。"""

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
    input[type="text"], select, textarea {{
      width: 100%; padding: 0.7rem; border: 1px solid var(--line);
      font: inherit; background: #fff;
    }}
    textarea {{ min-height: 110px; resize: vertical; }}
    .hint {{ color: var(--muted); font-size: 0.88rem; margin: 0.35rem 0 0.7rem; }}
    .row {{ display: flex; flex-wrap: wrap; gap: 0.6rem; margin-top: 0.7rem; }}
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
    <p class="meta">可编辑大词典与对照表词汇，也可新建对照表。不能新增大词典文件。</p>
    <p class="meta"><a href="{home}">← 返回首页</a></p>
    {msg_html}
    {err_html}

    <section class="panel">
      <h2>编辑大词典（scowl_words.txt）</h2>
      <form method="post" action="{action}">
        <input type="hidden" name="action" value="edit_dict" />
        <label for="dict_add">添加单词（每行一个）</label>
        <textarea id="dict_add" name="add_words" placeholder="apple&#10;banana"></textarea>
        <label for="dict_remove">删除单词（每行一个）</label>
        <textarea id="dict_remove" name="remove_words" placeholder="obsoleteword"></textarea>
        <div class="row"><button type="submit">更新大词典</button></div>
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
      <h2>新建对照表</h2>
      <form method="post" action="{action}">
        <input type="hidden" name="action" value="create_wordlist" />
        <label for="new_list">名称</label>
        <input id="new_list" name="new_name" type="text" placeholder="例如 cet4 或 考研词汇" />
        <p class="hint">将保存为 wordlists/名称.txt。不能用于新增大词典。</p>
        <div class="row"><button type="submit">创建对照表</button></div>
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
