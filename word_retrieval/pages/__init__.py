"""页面渲染模块。"""

ICP_NUMBER = "蜀ICP备2026058519号"
ICP_URL = "https://beian.miit.gov.cn/"

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
    .site-footer a {
      color: #5a6b75;
      text-decoration: none;
      font-weight: 400;
    }
    .site-footer a:hover { text-decoration: underline; }
"""


def icp_footer_html() -> str:
    """页脚 HTML：备案号链至工信部查询站。"""
    return (
        f'<footer class="site-footer">'
        f'<a href="{ICP_URL}" target="_blank" rel="noopener noreferrer">'
        f"{ICP_NUMBER}</a></footer>"
    )
