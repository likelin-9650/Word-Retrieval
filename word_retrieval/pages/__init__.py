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
