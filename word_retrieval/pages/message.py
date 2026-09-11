"""生成提示界面。"""

from __future__ import annotations

import html

from flask import url_for


def render_message_page(title: str, message: str, status: int = 400):
    """生成简单提示页面。"""
    home = url_for("main.index")
    body = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(title)}</title>
  <style>
    body {{
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
      background: linear-gradient(165deg, #e8f0f4, #f7f3ec);
      color: #1c2a32;
      padding: 1.5rem;
    }}
    main {{
      width: min(520px, 100%);
      background: rgba(255, 255, 255, 0.8);
      border: 1px solid #c5d2da;
      padding: 1.4rem;
    }}
    a {{ color: #0f6a5c; font-weight: 600; }}
  </style>
</head>
<body>
  <main>
    <h1>{html.escape(title)}</h1>
    <p>{html.escape(message)}</p>
    <p><a href="{home}">← 返回重新上传</a></p>
  </main>
</body>
</html>
"""
    return body, status
