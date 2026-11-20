# SECURITY 3.1：健康检查与优雅重启

## 范围

- **做（已实现 / 文档已写）**
  - 保持 `GET /healthz`：轻量存活，`{"ok": true}`；不加载 ECDICT、不扫 `.cache`。
  - `.github/DEPLOY.md`：systemd/gunicorn 优雅停机参数；Nginx `upstream` + 短连接超时 + `proxy_next_upstream`（须服务器手动改）。
  - `.github/workflows/deploy.yml`：`systemctl restart` 后最多约 30s 轮询本机 `/healthz`，失败则部署失败。
- **不做**
  - ECDICT readiness / `/readyz`；Actions 不改线上 unit 或 Nginx 文件；不改业务路由与确认页勾选。

## 决策

- 部署探活：方案 **B**（Actions 轮询轻量 `/healthz`）。
- `/healthz` 保持轻量（不做词典预热）。

## 服务器手动操作

### systemd

编辑 `/etc/systemd/system/word-retrieval.service`（路径以实机为准），对齐 DEPLOY 示例：

- `TimeoutStopSec=60`、`KillMode=mixed`
- gunicorn：`--timeout 120 --graceful-timeout 30`，仍 `-w 2 -b 127.0.0.1:5000`

然后：

```bash
sudo systemctl daemon-reload
sudo systemctl restart word-retrieval
curl -s http://127.0.0.1:5000/healthz
```

### Nginx

站点配置增加 `upstream word_retrieval { server 127.0.0.1:5000; }`，各 `location` 的 `proxy_pass` 指向该 upstream，并设短 `proxy_connect_timeout` 与 `proxy_next_upstream`（见 DEPLOY 第七节）。然后：

```bash
sudo nginx -t && sudo systemctl reload nginx
```

Actions **不会**改 unit / Nginx。

## 验收

- `/healthz` 返回 `{"ok":true}`，不加载 ECDICT。
- 部署日志在 restart 后出现 `healthz ok`；进程起不来则 workflow 失败。
- 按文档改 unit/Nginx 后，重启窗口行为与示例一致。

## 落地记录

- 日期：2026-11-20
- 状态：已实现（应用侧 healthz 沿用 1.3；文档 + deploy 探活；线上 unit/Nginx 须手动）
