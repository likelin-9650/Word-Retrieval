"""人工确认页面。"""

from __future__ import annotations

import html

from flask import url_for

from word_retrieval.pages import (
    EXCHANGE_HELP_CSS,
    EXCHANGE_HELP_JS,
    ICP_FOOTER_CSS,
    exchange_field_html,
    icp_footer_html,
)


def _dual_target_yellow_list(words: list[str]) -> str:
    if not words:
        return '<p class="empty">无</p>'
    exchange_input = (
        '<input type="text" class="dict-exchange" '
        'placeholder="如 s:apples/p:apple" />'
    )
    exchange_block = exchange_field_html(
        input_html=exchange_input,
        label_text="词形变化",
    )
    items = []
    for word in words:
        w = html.escape(word)
        wid = html.escape(word, quote=True)
        items.append(
            f'<div class="word-block proper" data-word="{wid}">'
            f'<div class="word-row">'
            f'<span class="term">{w}</span>'
            f'<label><input type="checkbox" name="yellow_to_words" value="{wid}" />对照表</label>'
            f'<label><input type="checkbox" name="yellow_to_dict" value="{wid}" '
            f'class="dict-toggle" />大词典</label>'
            f"</div>"
            f'<div class="dict-fields" hidden>'
            f'<p class="field-hint">加入大词典须填写与 ECDICT 对齐的词条：'
            f'<strong>中文释义必填</strong>（请在释义中同时写上词性，如 '
            f'<code>n. 苹果</code>）；音标、英文释义、词形变化可选。</p>'
            f'<label>中文释义 <span class="req">*</span>'
            f'<span class="field-subhint">请同时写上词性，例如：n. 苹果 / v. 运行</span>'
            f'<textarea class="dict-translation" rows="2" '
            f'placeholder="n. 苹果"></textarea></label>'
            f'<div class="field-grid">'
            f'<label>音标'
            f'<input type="text" class="dict-phonetic" placeholder="如 ˈæpl 或 /ˈæpl/" /></label>'
            f"{exchange_block}"
            f"</div>"
            f'<label>英文释义'
            f'<textarea class="dict-definition" rows="2" '
            f'placeholder="可选，英文义项"></textarea></label>'
            f"</div>"
            f"</div>"
        )
    return '<div class="word-rows">\n' + "\n".join(items) + "\n</div>"


def _green_list(words: list[str]) -> str:
    if not words:
        return '<p class="empty">无</p>'
    items = []
    for word in words:
        w = html.escape(word)
        wid = html.escape(word, quote=True)
        items.append(
            f'<div class="word-row known">'
            f'<span class="term">{w}</span>'
            f'<label><input type="checkbox" name="green_to_vocab" value="{wid}" />进入释义表</label>'
            f'<label><input type="checkbox" name="green_remove_words" value="{wid}" />剔出对照表</label>'
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
    footer = icp_footer_html()

    green_html = _green_list(green_sorted)
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
    .word-block {{
      border-bottom: 1px solid rgba(197, 210, 218, 0.55);
      padding-bottom: 0.45rem;
    }}
    .word-row {{
      display: grid;
      grid-template-columns: minmax(100px, 1.2fr) auto auto;
      gap: 0.75rem;
      align-items: center;
      padding: 0.35rem 0.45rem;
      border-bottom: 1px solid rgba(197, 210, 218, 0.55);
    }}
    .word-block .word-row {{ border-bottom: 0; }}
    .word-row .term {{ font-weight: 600; }}
    .word-row.known .term, .word-block.known .term {{ color: var(--known); }}
    .word-row.proper .term, .word-block.proper .term {{ color: var(--proper); }}
    .word-row.unknown .term, .word-block.unknown .term {{ color: var(--unknown); }}
    .dict-fields {{
      margin: 0.25rem 0.45rem 0.55rem;
      padding: 0.75rem 0.85rem;
      background: rgba(196, 160, 0, 0.08);
      border: 1px solid rgba(196, 160, 0, 0.28);
      display: grid;
      gap: 0.55rem;
    }}
    .dict-fields .field-hint {{
      margin: 0; color: var(--muted); font-size: 0.85rem; line-height: 1.45;
    }}
    .dict-fields .field-subhint {{
      display: block; font-weight: 400; color: var(--muted); font-size: 0.8rem;
    }}
    .dict-fields .req {{ color: var(--unknown); }}
    .dict-fields code {{
      font-family: Consolas, "Courier New", monospace; font-size: 0.9em;
      background: rgba(28, 77, 110, 0.06); padding: 0.05rem 0.25rem;
    }}
    .dict-fields label {{
      display: grid; gap: 0.25rem; font-size: 0.88rem; font-weight: 600;
    }}
    .dict-fields input, .dict-fields textarea {{
      width: 100%; font: inherit; font-weight: 400; padding: 0.45rem 0.55rem;
      border: 1px solid var(--line); background: #fff;
    }}
    .dict-fields textarea {{ resize: vertical; }}
    .dict-fields .exchange-field {{ grid-column: 1 / -1; }}
    .field-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 0.55rem;
    }}
{EXCHANGE_HELP_CSS}
    .empty {{ color: var(--muted); margin: 0; }}
    .form-error {{
      color: var(--unknown); margin: 0.6rem 0 0; font-size: 0.92rem; display: none;
    }}
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
{ICP_FOOTER_CSS}
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

      <section class="panel" data-group="green">
        <h2 style="color:var(--known)">绿色词 — 释义表与剔出对照表分开选择</h2>
        <p class="hint">这些词已在对照表中。「进入释义表」会写入本次释义表；「剔出对照表」会从<strong>本浏览器</strong>对照表差分中删除该词。两项均默认不勾选。</p>
        <div class="toolbar">
          <button type="button" data-action="vocab-all">释义表全选</button>
          <button type="button" data-action="vocab-none">释义表全不选</button>
          <button type="button" data-action="remove-all">剔出全选</button>
          <button type="button" data-action="remove-none">剔出全不选</button>
        </div>
        {green_html}
      </section>

      <section class="panel" data-group="yellow">
        <h2 style="color:var(--proper)">黄色词 — 可加入对照表 / 大词典（ECDICT 增补） / 二者都加</h2>
        <p class="hint">每个词可单独勾选目标；两者都勾选即同时加入。<strong>写入本浏览器</strong>，不改服务器基准文件。勾选「大词典」时须填写<strong>中文释义</strong>（请在释义里写上词性，如 n. 苹果；音标、英文释义、词形变化可选）。</p>
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
        <p class="hint">「进入释义表」默认勾选；「加入对照表」默认不勾选（保存到本浏览器）。释义来自服务器 ECDICT。</p>
        <div class="toolbar">
          <button type="button" data-action="keep-all">释义表全选</button>
          <button type="button" data-action="keep-none">释义表全不选</button>
          <button type="button" data-action="words-all">对照表全选</button>
          <button type="button" data-action="words-none">对照表全不选</button>
        </div>
        {red_html}
      </section>

      <input type="hidden" name="yellow_dict_entries" id="yellow_dict_entries" value="[]" />
      <p class="form-error" id="formError"></p>
      <div class="actions">
        <button class="submit" type="submit">确认并生成文档</button>
        <a href="{home}">← 返回重来</a>
      </div>
    </form>
  </main>
  {footer}
  <script>
    document.querySelectorAll('.panel[data-group="green"]').forEach((panel) => {{
      panel.querySelectorAll("button[data-action]").forEach((btn) => {{
        btn.addEventListener("click", () => {{
          const action = btn.getAttribute("data-action");
          if (action === "vocab-all" || action === "vocab-none") {{
            const on = action === "vocab-all";
            panel.querySelectorAll('input[name="green_to_vocab"]').forEach((box) => {{
              box.checked = on;
            }});
          }}
          if (action === "remove-all" || action === "remove-none") {{
            const on = action === "remove-all";
            panel.querySelectorAll('input[name="green_remove_words"]').forEach((box) => {{
              box.checked = on;
            }});
          }}
        }});
      }});
    }});

    function syncDictFields(block) {{
      const toggle = block.querySelector(".dict-toggle");
      const fields = block.querySelector(".dict-fields");
      if (!toggle || !fields) return;
      fields.hidden = !toggle.checked;
    }}

    const yellowPanel = document.querySelector('.panel[data-group="yellow"]');
    if (yellowPanel) {{
      yellowPanel.querySelectorAll(".word-block").forEach((block) => {{
        const toggle = block.querySelector(".dict-toggle");
        if (toggle) {{
          toggle.addEventListener("change", () => syncDictFields(block));
          syncDictFields(block);
        }}
      }});
      yellowPanel.querySelectorAll("button[data-action]").forEach((btn) => {{
        btn.addEventListener("click", () => {{
          const action = btn.getAttribute("data-action");
          if (action === "words-all" || action === "words-none") {{
            const on = action === "words-all";
            yellowPanel.querySelectorAll('input[name="yellow_to_words"]').forEach((b) => b.checked = on);
          }}
          if (action === "dict-all" || action === "dict-none") {{
            const on = action === "dict-all";
            yellowPanel.querySelectorAll('input[name="yellow_to_dict"]').forEach((b) => {{
              b.checked = on;
              const block = b.closest(".word-block");
              if (block) syncDictFields(block);
            }});
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

    const confirmForm = document.querySelector("form");
    const formError = document.getElementById("formError");
    const entriesInput = document.getElementById("yellow_dict_entries");
    if (confirmForm && entriesInput) {{
      confirmForm.addEventListener("submit", (ev) => {{
        const entries = [];
        const missing = [];
        document.querySelectorAll('.panel[data-group="yellow"] .word-block').forEach((block) => {{
          const toggle = block.querySelector(".dict-toggle");
          if (!toggle || !toggle.checked) return;
          const word = (block.getAttribute("data-word") || toggle.value || "").trim().toLowerCase();
          const translation = (block.querySelector(".dict-translation")?.value || "").trim();
          const phonetic = (block.querySelector(".dict-phonetic")?.value || "").trim();
          const definition = (block.querySelector(".dict-definition")?.value || "").trim();
          const exchange = (block.querySelector(".dict-exchange")?.value || "").trim();
          if (!translation) {{
            missing.push(word);
            return;
          }}
          entries.push({{
            word,
            translation,
            pos: "",
            phonetic,
            definition,
            exchange,
          }});
        }});
        if (missing.length) {{
          ev.preventDefault();
          formError.style.display = "block";
          formError.textContent =
            "勾选「大词典」的词须填写中文释义（请同时写上词性，如 n. 苹果）："
            + missing.slice(0, 8).join("、")
            + (missing.length > 8 ? "…" : "");
          return;
        }}
        formError.style.display = "none";
        formError.textContent = "";
        entriesInput.value = JSON.stringify(entries);
      }});
    }}
{EXCHANGE_HELP_JS}
  </script>
</body>
</html>
"""
