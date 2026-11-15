# SECURITY 1.1 问题 3+4：缓存上限与一次下载

## 范围

- **问题 3**：同时会话上限 **50**；`.cache` 合计约 **500MB**；超限友好拒绝（503）；启动时扫过期项；请求路径仍惰性清理。
- **问题 4**：TTL **30 分钟**（1800s）；**首次下载后删除**；结果页提示。
- **不做**：Redis；token 绑定账号/签名；定时独立 cron（启动 + 惰性已够）。

## 实现要点

- `job_cache.py`：`DEFAULT_MAX_AGE_SEC=1800`；`CacheLimitError`；`count_active_sessions` / `cache_total_bytes` / `ensure_cache_capacity`
- `__init__.py`：`CACHE_MAX_AGE_SEC` / `CACHE_MAX_SESSIONS` / `CACHE_MAX_BYTES`；启动 `cleanup_expired`
- `routes.py`：建会话与存下载前容量检查；`download_file` 读入内存后 `delete_download`
- `pages/result.py`：一次下载 + 30 分钟提示
- 文档：README / HANDOFF / SECURITY_STABILITY / privacy

## 验收

- 超过会话数或缓存体积时 upload/confirm 生成阶段返回友好错误
- 同一 download token 第二次访问为过期/已下载
- TTL 文档与配置均为 30 分钟

## 落地记录

- 日期：2026-11-15
- 状态：已实现
