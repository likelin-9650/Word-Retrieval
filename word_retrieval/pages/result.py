"""生成单词提取结果展示页面。"""

from __future__ import annotations

import html

from flask import url_for


def render_result_page(
    source_label: str,
    green_words: set[str],
    yellow_words: set[str],
    red_words: set[str],
    *,
    highlight_token: str | None = None,
    highlight_name: str | None = None,
    vocab_token: str | None = None,
    vocab_name: str | None = None,
    translate_error: str | None = None,
    saved_count: int = 0,
    removed_count: int = 0,
) -> str:
    """生成展示提取结果的 HTML 页面。"""
    green_sorted = sorted(green_words)
    yellow_sorted = sorted(yellow_words)
    red_sorted = sorted(red_words)
    total = len(green_sorted) + len(yellow_sorted) + len(red_sorted)
    home = url_for("main.index")

    def render_list(words: list[str], css_class: str, empty_text: str) -> str:
        if not words:
            return f'        <li class="empty">{html.escape(empty_text)}</li>'
        return "\n".join(
            f'        <li class="{css_class}">{html.escape(word)}</li>' for word in words
        )

    green_items = render_list(green_sorted, "known", "无绿色单词")
    yellow_items = render_list(yellow_sorted, "proper", "无黄色单词")
    red_items = render_list(red_sorted, "unknown", "无进入释义表的单词")

    actions: list[str] = []
    if highlight_token and highlight_name:
        highlight_url = url_for("main.download_file", token=highlight_token)
        actions.append(
            f'<a class="download-btn" href="{highlight_url}" '
            f'download="{html.escape(highlight_name)}">下载标注后的 Word 文档</a>'
        )
    if vocab_token and vocab_name:
        vocab_url = url_for("main.download_file", token=vocab_token)
        actions.append(
            f'<a class="download-btn secondary" href="{vocab_url}" '
            f'download="{html.escape(vocab_name)}">下载未掌握单词释义表</a>'
        )

    actions_html = "\n      ".join(actions) if actions else ""
    hint = (
        '<span class="hint">点击后浏览器会询问保存位置（另存为）</span>'
        if actions
        else ""
    )
    error_html = (
        f'<p class="error">{html.escape(translate_error)}</p>'
        if translate_error
        else ""
    )
    status_bits: list[str] = []
    if saved_count:
        status_bits.append(f"已写入对照表/大词典覆盖 <strong>{saved_count}</strong> 个词")
    if removed_count:
        status_bits.append(f"已从对照表剔除 <strong>{removed_count}</strong> 个词")
    saved_html = (
        f'<p class="meta">{"；".join(status_bits)}。</p>' if status_bits else ""
    )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>提取结果</title>
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
      margin: 0;
      min-height: 100vh;
      font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at 12% 18%, rgba(15, 106, 92, 0.12), transparent 42%),
        linear-gradient(165deg, var(--bg-top), var(--bg-bottom));
      padding: 2rem 1rem 3rem;
    }}
    main {{ width: min(760px, 100%); margin: 0 auto; }}
    h1 {{ margin: 0 0 0.4rem; font-size: clamp(1.8rem, 4vw, 2.4rem); }}
    h2 {{ margin: 0 0 0.7rem; font-size: 1.1rem; }}
    .meta {{ color: var(--muted); margin: 0 0 1.2rem; line-height: 1.5; }}
    a {{ color: var(--accent); font-weight: 600; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .actions {{
      display: flex; flex-wrap: wrap; gap: 0.8rem; margin: 0 0 1.4rem; align-items: center;
    }}
    .download-btn {{
      display: inline-block; background: var(--accent); color: #fff !important;
      text-decoration: none !important; padding: 0.75rem 1.1rem; font-weight: 600;
    }}
    .download-btn.secondary {{ background: #1c4d6e; }}
    .download-btn:hover {{ background: var(--accent-hover); }}
    .download-btn.secondary:hover {{ background: #163d57; }}
    .hint {{ color: var(--muted); font-size: 0.9rem; }}
    .error {{ color: var(--unknown); margin: 0 0 1rem; line-height: 1.5; }}
    .legend {{ display: flex; flex-wrap: wrap; gap: 1.2rem; margin: 0 0 1rem; }}
    .legend .known {{ color: var(--known); font-weight: 600; }}
    .legend .proper {{ color: var(--proper); font-weight: 600; }}
    .legend .unknown {{ color: var(--unknown); font-weight: 600; }}
    .panel {{
      background: var(--surface); border: 1px solid var(--line);
      padding: 1.2rem 1.4rem; margin-bottom: 1rem;
    }}
    ul {{
      margin: 0; padding-left: 1.2rem; columns: 2; column-gap: 2rem;
    }}
    li {{ break-inside: avoid; margin: 0.25rem 0; line-height: 1.4; }}
    li.known {{ color: var(--known); }}
    li.proper {{ color: var(--proper); }}
    li.unknown {{ color: var(--unknown); }}
    li.empty {{
      list-style: none; margin-left: -1.2rem; color: var(--muted);
    }}
    @media (max-width: 560px) {{ ul {{ columns: 1; }} }}
  </style>
</head>
<body>
  <main>
    <h1>提取结果</h1>
    <p class="meta">
      来源：{html.escape(source_label)}<br />
      共 <strong>{total}</strong> 个不重复英语单词：
      <span style="color:var(--known)">绿 {len(green_sorted)}</span>，
      <span style="color:var(--proper)">黄 {len(yellow_sorted)}</span>，
      <span style="color:var(--unknown)">红 {len(red_sorted)}</span>
    </p>
    {saved_html}

    <div class="actions">
      {actions_html}
      {hint}
    </div>
    {error_html}

    <p class="meta"><a href="{home}">← 返回继续处理</a></p>

    <div class="legend">
      <span class="known">绿 = 已掌握</span>
      <span class="proper">黄 = 不在大词典（ECDICT）</span>
      <span class="unknown">进入释义表的词（红词确认 + 绿词勾选）</span>
    </div>

    <section class="panel">
      <h2>绿色</h2>
      <ul>
{green_items}
      </ul>
    </section>
    <section class="panel">
      <h2>黄色</h2>
      <ul>
{yellow_items}
      </ul>
    </section>
    <section class="panel">
      <h2>进入释义表的词</h2>
      <ul>
{red_items}
      </ul>
    </section>
  </main>
</body>
</html>
"""
