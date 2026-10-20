"""页面渲染模块。"""

from flask import url_for

ICP_NUMBER = "蜀ICP备2026058519号"
ICP_URL = "https://beian.miit.gov.cn/"

MPS_NUMBER = "川公网安备51070302110809号"
MPS_URL = "https://beian.mps.gov.cn/#/query/webSearch?code=51070302110809"
MPS_ICON = "beian-mps.png"

# 经 f-string 的 {变量} 注入；内容中的花括号不会被二次解析。
ICP_FOOTER_CSS = """
    .site-footer {
      margin-top: 1.75rem;
      padding: 0.25rem 0 0.5rem;
      text-align: center;
      font-size: 0.85rem;
      color: #5a6b75;
      line-height: 1.5;
    }
    .site-footer .beian-lines {
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      align-items: center;
      gap: 0.35rem 1.1rem;
    }
    .site-footer a {
      color: #5a6b75;
      text-decoration: none;
      font-weight: 400;
      display: inline-flex;
      align-items: center;
      gap: 0.3rem;
    }
    .site-footer a:hover { text-decoration: underline; }
    .site-footer .beian-icon {
      width: 16px;
      height: 16px;
      vertical-align: middle;
      flex-shrink: 0;
    }
"""


def icp_footer_html() -> str:
    """页脚 HTML：工信部 ICP + 公安备案（含图标）。"""
    icon_url = url_for("static", filename=MPS_ICON)
    return (
        f'<footer class="site-footer">'
        f'<div class="beian-lines">'
        f'<a href="{ICP_URL}" target="_blank" rel="noopener noreferrer">'
        f"{ICP_NUMBER}</a>"
        f'<a href="{MPS_URL}" rel="noreferrer" target="_blank">'
        f'<img class="beian-icon" src="{icon_url}" alt="" width="16" height="16" />'
        f"{MPS_NUMBER}</a>"
        f"</div></footer>"
    )


# ECDICT exchange（词形变化）说明：确认页 / 设置页共用
EXCHANGE_HELP_CSS = """
    .exchange-field { display: grid; gap: 0.25rem; }
    .exchange-label-row {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 0.45rem;
      font-size: 0.88rem;
      font-weight: 600;
    }
    .exchange-help-btn {
      appearance: none;
      border: 1px solid #c5d2da;
      background: #fff;
      color: #0f6a5c;
      font: inherit;
      font-size: 0.8rem;
      font-weight: 600;
      padding: 0.15rem 0.5rem;
      cursor: pointer;
      line-height: 1.3;
    }
    .exchange-help-btn:hover { background: rgba(15, 106, 92, 0.08); }
    .exchange-help {
      margin: 0.15rem 0 0;
      padding: 0.65rem 0.75rem;
      border: 1px solid #c5d2da;
      background: rgba(255, 255, 255, 0.92);
      color: #5a6b75;
      font-size: 0.82rem;
      font-weight: 400;
      line-height: 1.5;
    }
    .exchange-help p { margin: 0 0 0.45rem; }
    .exchange-help p:last-child { margin-bottom: 0; }
    .exchange-help ul {
      margin: 0.2rem 0 0.45rem;
      padding-left: 1.1rem;
    }
    .exchange-help code {
      font-family: Consolas, "Courier New", monospace;
      font-size: 0.9em;
      background: rgba(28, 77, 110, 0.06);
      padding: 0.05rem 0.25rem;
    }
"""

EXCHANGE_HELP_BODY = """
<p>对应 ECDICT 的 <code>exchange</code> 字段：用标签记录该词的屈折/派生形态，多项用 <code>/</code> 连接。</p>
<p>格式：<code>标签:词形</code>，例如 <code>s:apples/p:ran/d:run/i:running/3:runs</code>。</p>
<ul>
  <li><code>p</code> 过去式</li>
  <li><code>d</code> / <code>pp</code> 过去分词</li>
  <li><code>i</code> / <code>ing</code> 现在分词 / 动名词</li>
  <li><code>3</code> 第三人称单数</li>
  <li><code>s</code> 名词复数</li>
  <li><code>r</code> 比较级 · <code>t</code> 最高级</li>
  <li><code>0</code> 词根 / 原形（lemma）</li>
</ul>
<p>选填；不确定可留空。此处只作词典备注，不会自动展开对照表。</p>
""".strip()

EXCHANGE_HELP_JS = """
    document.addEventListener("click", (ev) => {
      const btn = ev.target.closest(".exchange-help-btn");
      if (!btn) return;
      ev.preventDefault();
      const root = btn.closest(".exchange-field");
      const panel = root && root.querySelector(".exchange-help");
      if (!panel) return;
      const willOpen = panel.hasAttribute("hidden");
      if (willOpen) panel.removeAttribute("hidden");
      else panel.setAttribute("hidden", "");
      btn.setAttribute("aria-expanded", willOpen ? "true" : "false");
    });
"""


def exchange_help_panel_html() -> str:
    """词形变化说明面板（配合 .exchange-help-btn 切换显示）。"""
    return f'<div class="exchange-help" hidden>{EXCHANGE_HELP_BODY}</div>'


def exchange_field_html(
    *,
    input_html: str,
    label_text: str,
    label_for: str | None = None,
) -> str:
    """
    词形变化输入区：标签行 +「说明」按钮 + 输入控件 + 可折叠说明。
    input_html 为完整的 input/textarea 标签字符串。
    """
    if label_for:
        label = f'<label for="{label_for}">{label_text}</label>'
    else:
        label = f"<span>{label_text}</span>"
    return (
        f'<div class="exchange-field">'
        f'<div class="exchange-label-row">'
        f"{label}"
        f'<button type="button" class="exchange-help-btn" '
        f'aria-expanded="false" title="查看 ECDICT 词形变化说明">说明</button>'
        f"</div>"
        f"{input_html}"
        f"{exchange_help_panel_html()}"
        f"</div>"
    )
