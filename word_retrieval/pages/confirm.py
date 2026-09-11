"""人工确认页面。"""

from __future__ import annotations

import html

from flask import url_for


def _dual_target_yellow_list(words: list[str]) -> str:
    if not words:
        return '<p class="empty">无</p>'
    items = []
    for word in words:
        w = html.escape(word)
        wid = html.escape(word, quote=True)
        items.append(
            f'<div class="word-row proper">'
            f'<span class="term">{w}</span>'
            f'<label><input type="checkbox" name="yellow_to_words" value="{wid}" />对照表</label>'
            f'<label><input type="checkbox" name="yellow_to_dict" value="{wid}" />大词典</label>'
            f"</div>"
        )
    return '<div class="word-rows">\n' + "\n".join(items) + "\n</div>"


def _red_list(words: list[str]) -> str:
    if not words:
        return '<p class="empty">无</p>'
    items = []
    for word in words:
        w = html.escape(word)
        wid = html.escape(word, quote=True)
        items.append(
            f'<div class="word-row unknown">'
            f'<span class="term">{w}</span>'
            f'<label><input type="checkbox" name="keep_red" value="{wid}" checked />进入释义表</label>'
            f'<label><input type="checkbox" name="red_to_words" value="{wid}" />加入对照表</label>'
            f"</div>"
        )
    return '<div class="word-rows">\n' + "\n".join(items) + "\n</div>"


def _checkbox_list(
    words: list[str],
    *,
    name: str,
    css: str,
    checked: bool,
) -> str:
    if not words:
        return '<p class="empty">无</p>'
    items = []
    checked_attr = " checked" if checked else ""
    for word in words:
        wid = html.escape(f"{name}_{word}", quote=True)
        w = html.escape(word)
        items.append(
            f'<label class="word {css}" for="{wid}">'
            f'<input id="{wid}" type="checkbox" name="{name}" value="{w}"{checked_attr} />'
            f"<span>{w}</span></label>"
        )
    return '<div class="word-grid">\n' + "\n".join(items) + "\n</div>"


def render_confirm_page(
    *,
    session_id: str,
    source_label: str,
    wordlist_name: str,
    green_words: set[str],
    yellow_words: set[str],
    red_words: set[str],
) -> str:
    green_sorted = sorted(green_words)
    yellow_sorted = sorted(yellow_words)
    red_sorted = sorted(red_words)
    total = len(green_sorted) + len(yellow_sorted) + len(red_sorted)
    home = url_for("main.index")
    action = url_for("main.confirm")

    green_html = _checkbox_list(
        green_sorted, name="save_green", css="known", checked=False
    )
    yellow_html = _dual_target_yellow_list(yellow_sorted)
    red_html = _red_list(red_sorted)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>人工确认</title>
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
      --known: #1b8f3a;
      --proper: #c4a000;
      --unknown: #c62828;
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
    main {{ width: min(920px, 100%); margin: 0 auto; }}
    h1 {{ margin: 0 0 0.4rem; font-size: clamp(1.7rem, 4vw, 2.2rem); }}
    h2 {{ margin: 0 0 0.55rem; font-size: 1.05rem; }}
    .meta {{ color: var(--muted); line-height: 1.5; margin: 0 0 1rem; }}
    a {{ color: var(--accent); font-weight: 600; text-decoration: none; }}
    .panel {{
      background: var(--surface); border: 1px solid var(--line);
      padding: 1rem 1.2rem; margin-bottom: 1rem;
    }}
    .hint {{ color: var(--muted); font-size: 0.9rem; margin: 0 0 0.8rem; }}
    .toolbar {{ display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.7rem; }}
    .toolbar button {{
      appearance: none; border: 1px solid var(--line); background: #fff;
      padding: 0.35rem 0.7rem; cursor: pointer; font: inherit;
    }}
    .word-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
      gap: 0.35rem 0.6rem;
    }}
    .word-rows {{ display: grid; gap: 0.45rem; }}
    .word-row {{
      display: grid;
      grid-template-columns: minmax(100px, 1.2fr) auto auto;
      gap: 0.75rem;
      align-items: center;
      padding: 0.35rem 0.45rem;
      border-bottom: 1px solid rgba(197, 210, 218, 0.55);
    }}
    .word-row .term {{ font-weight: 600; }}
    .word-row.proper .term {{ color: var(--proper); }}
    .word-row.unknown .term {{ color: var(--unknown); }}
    label.word {{
      display: flex; align-items: center; gap: 0.4rem;
      font-size: 0.95rem; line-height: 1.3;
    }}
    label.word.known span {{ color: var(--known); }}
    .empty {{ color: var(--muted); margin: 0; }}
    .actions {{
      display: flex; flex-wrap: wrap; gap: 0.8rem; align-items: center; margin-top: 1rem;
    }}
    .submit {{
      appearance: none; border: 0; background: var(--accent); color: #fff;
      font: inherit; font-weight: 600; padding: 0.8rem 1.1rem; cursor: pointer;
    }}
    .submit:hover {{ background: var(--accent-hover); }}
    @media (max-width: 640px) {{
      .word-row {{ grid-template-columns: 1fr; gap: 0.3rem; }}
    }}
  </style>
</head>
<body>
  <main>
    <h1>人工确认</h1>
    <p class="meta">
      来源：{html.escape(source_label)}<br />
      对照表：{html.escape(wordlist_name)}<br />
      共 {total} 个词 —
      <span style="color:var(--known)">绿 {len(green_sorted)}</span> /
      <span style="color:var(--proper)">黄 {len(yellow_sorted)}</span> /
      <span style="color:var(--unknown)">红 {len(red_sorted)}</span>
    </p>

    <form method="post" action="{action}">
      <input type="hidden" name="session_id" value="{html.escape(session_id)}" />

      <section class="panel" data-group="save_green">
        <h2 style="color:var(--known)">绿色词 — 勾选后写入当前对照表</h2>
        <p class="hint">默认不勾选。需要补录时再勾选。</p>
        <div class="toolbar">
          <button type="button" data-action="all">全选</button>
          <button type="button" data-action="none">全不选</button>
        </div>
        {green_html}
      </section>

      <section class="panel" data-group="yellow">
        <h2 style="color:var(--proper)">黄色词 — 可加入对照表 / 大词典 / 二者都加</h2>
        <p class="hint">每个词可单独勾选目标；两者都勾选即同时加入。</p>
        <div class="toolbar">
          <button type="button" data-action="words-all">对照表全选</button>
          <button type="button" data-action="words-none">对照表全不选</button>
          <button type="button" data-action="dict-all">大词典全选</button>
          <button type="button" data-action="dict-none">大词典全不选</button>
        </div>
        {yellow_html}
      </section>

      <section class="panel" data-group="red">
        <h2 style="color:var(--unknown)">红色词 — 释义表与对照表分开选择</h2>
        <p class="hint">「进入释义表」默认勾选；「加入对照表」默认不勾选，可另选保存。释义来自本地 ECDICT。</p>
        <div class="toolbar">
          <button type="button" data-action="keep-all">释义表全选</button>
          <button type="button" data-action="keep-none">释义表全不选</button>
          <button type="button" data-action="words-all">对照表全选</button>
          <button type="button" data-action="words-none">对照表全不选</button>
        </div>
        {red_html}
      </section>

      <div class="actions">
        <button class="submit" type="submit">确认并生成文档</button>
        <a href="{home}">← 返回重来</a>
      </div>
    </form>
  </main>
  <script>
    document.querySelectorAll('.panel[data-group="save_green"]').forEach((panel) => {{
      panel.querySelectorAll("button[data-action]").forEach((btn) => {{
        btn.addEventListener("click", () => {{
          const on = btn.getAttribute("data-action") === "all";
          panel.querySelectorAll('input[name="save_green"]').forEach((box) => {{
            box.checked = on;
          }});
        }});
      }});
    }});

    const yellowPanel = document.querySelector('.panel[data-group="yellow"]');
    if (yellowPanel) {{
      yellowPanel.querySelectorAll("button[data-action]").forEach((btn) => {{
        btn.addEventListener("click", () => {{
          const action = btn.getAttribute("data-action");
          if (action === "words-all" || action === "words-none") {{
            const on = action === "words-all";
            yellowPanel.querySelectorAll('input[name="yellow_to_words"]').forEach((b) => b.checked = on);
          }}
          if (action === "dict-all" || action === "dict-none") {{
            const on = action === "dict-all";
            yellowPanel.querySelectorAll('input[name="yellow_to_dict"]').forEach((b) => b.checked = on);
          }}
        }});
      }});
    }}

    const redPanel = document.querySelector('.panel[data-group="red"]');
    if (redPanel) {{
      redPanel.querySelectorAll("button[data-action]").forEach((btn) => {{
        btn.addEventListener("click", () => {{
          const action = btn.getAttribute("data-action");
          if (action === "keep-all" || action === "keep-none") {{
            const on = action === "keep-all";
            redPanel.querySelectorAll('input[name="keep_red"]').forEach((b) => b.checked = on);
          }}
          if (action === "words-all" || action === "words-none") {{
            const on = action === "words-all";
            redPanel.querySelectorAll('input[name="red_to_words"]').forEach((b) => b.checked = on);
          }}
        }});
      }});
    }}
  </script>
</body>
</html>
"""
