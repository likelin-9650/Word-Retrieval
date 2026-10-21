"""隐私说明页面。"""

from __future__ import annotations

from flask import url_for

from word_retrieval.pages import ICP_FOOTER_CSS, icp_footer_html


def render_privacy_page() -> str:
    home = url_for("main.index")
    settings = url_for("main.settings")
    footer = icp_footer_html()
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>隐私说明</title>
  <style>
    :root {{
      --bg-top: #e8f0f4;
      --bg-bottom: #f7f3ec;
      --ink: #1c2a32;
      --muted: #5a6b75;
      --accent: #0f6a5c;
      --line: #c5d2da;
      --surface: rgba(255, 255, 255, 0.72);
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
    main {{
      width: min(680px, 100%);
      margin: 0 auto;
      background: var(--surface);
      border: 1px solid var(--line);
      padding: 1.3rem 1.4rem 1.5rem;
    }}
    h1 {{ margin: 0 0 0.5rem; font-size: 1.35rem; }}
    h2 {{ margin: 1.25rem 0 0.45rem; font-size: 1.05rem; }}
    p, li {{ color: var(--ink); line-height: 1.6; }}
    .meta {{ color: var(--muted); margin: 0 0 1rem; line-height: 1.5; }}
    a {{ color: var(--accent); font-weight: 600; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    ul {{ margin: 0.35rem 0 0.7rem; padding-left: 1.25rem; }}
    li {{ margin: 0.25rem 0; }}
    code {{
      font-family: Consolas, "Courier New", monospace; font-size: 0.9em;
      background: rgba(28, 77, 110, 0.06); padding: 0.05rem 0.25rem;
    }}
{ICP_FOOTER_CSS}
  </style>
</head>
<body>
  <main>
    <h1>隐私说明</h1>
    <p class="meta">
      本页说明本站如何使用浏览器本地存储，以及提交内容时服务器如何处理数据。
      <a href="{home}">← 返回首页</a>
      ·
      <a href="{settings}">设置</a>
    </p>

    <h2>浏览器本地存储</h2>
    <p>
      本站使用浏览器的 <code>localStorage</code>
      （键名 <code>word-retrieval-user-data</code> 等）保存你的个人偏好与差分数据，
      <strong>仅保存在当前浏览器</strong>，不会写入服务器上的共享对照表或 ECDICT 数据库。
    </p>
    <p>本地可能保存的内容包括：</p>
    <ul>
      <li>对服务器基准对照表的增删差分、本机自建对照表；</li>
      <li>大词典的本机增补词条与排除列表；</li>
      <li>绿 / 黄 / 红着色颜色与「是否在 Word 中着色」开关；</li>
      <li>你上次选择的对照表名称。</li>
    </ul>
    <p>用途：记住你的掌握词表与显示偏好，便于下次继续使用，无需注册账号。</p>

    <h2>提交文章或文档时</h2>
    <p>
      上传或粘贴文本提取单词时，浏览器会把上述本机差分一并提交给服务器，
      仅用于<strong>当次</strong>分类、确认页展示、生成着色 Word 与释义表。
      服务器<strong>不会</strong>把这些个人差分当作用户档案长期保存到共享词表或词典文件中。
    </p>
    <p>
      生成的下载文件（着色文档、释义表）会在服务器临时缓存约
      <strong>1 小时</strong>，过期后清理；会话数据同样有时效。
    </p>

    <h2>数据丢失与备份</h2>
    <p>
      换浏览器、清除站点数据、使用无痕模式，或在
      <a href="{settings}">设置</a> 中「清除本机全部改动」，都会丢失本机保存的内容。
      换设备前请在设置页使用<strong>导出 JSON</strong>备份，并在新环境<strong>导入</strong>恢复。
    </p>

    <h2>我们不做什么</h2>
    <ul>
      <li>不要求注册登录或提供手机号、邮箱；</li>
      <li>不把本机词表/偏好同步为服务器端用户账号数据；</li>
      <li>不为广告目的收集与学习功能无关的设备指纹或精准定位。</li>
    </ul>

    <p class="meta" style="margin-top:1.25rem;margin-bottom:0">
      若后续增加账号、云同步等功能，将另行更新本说明。
    </p>
  </main>
  {footer}
</body>
</html>
"""
