---
name: 可观测性 3.2
overview: 补上 SECURITY 3.2：JSON 一行一条日志、request id、响应头 X-Request-ID；替换裸 print；业务/意外异常分级；/healthz 不打 INFO。不做远程采集或改 Nginx。
todos:
  - id: plan-docs
    content: 10 方案 md + .plan.md 备份
    status: completed
  - id: logging-module
    content: request_logging：JSON Formatter、before/after_request、X-Request-ID、healthz 静默
    status: completed
  - id: routes
    content: 去掉 print；分类摘要/CSRF/缓存超限分级 logger
    status: completed
  - id: sync-docs
    content: SECURITY_STABILITY / HANDOFF / README 中英 / privacy；README.docx
    status: completed
isProject: false
---

# 3.2 可观测性

## 范围

- **做**
  - 应用层 JSON 一行一条日志（stderr → gunicorn/journald）。
  - 每请求生成 `request_id`，写入日志字段，响应头 `X-Request-ID`。
  - 替换 `_begin_review` 裸 `print`；CSRF 失败 / 缓存超限 / 意外异常分级可区分。
  - `GET /healthz` 不打 INFO 访问日志。
- **不做**
  - 远程日志采集、ELK、改 Nginx access_log、改 gunicorn access log 过滤。
  - 记录粘贴正文、`user_data` JSON、CSRF 密钥。
  - 改确认页勾选、着色/释义表、CSP、下载硬化逻辑。
  - 给 `job_cache` 静默 `OSError` 补日志（属更大范围 C，本次不做）。

## 决策（用户确认）

1. 范围 **A**（结构化 + request id，非仅换 print）。
2. 回写 **`X-Request-ID`**。
3. 日志格式 **JSON 一行一条**。
4. 隐私：只记路径/状态/词数等元数据。
5. **`/healthz` 保持静默**（无 INFO 访问日志）。

## 实现要点

见 [`10-observability.md`](10-observability.md)。
