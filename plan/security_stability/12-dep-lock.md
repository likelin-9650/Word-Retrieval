# SECURITY 3.5：依赖锁定

## 范围

- **做（已实现）**
  - [`requirements.txt`](../../requirements.txt) 全部 `包==版本`（本机 `.venv` 的 `pip freeze`，含 lxml/numpy 等传递依赖）。
  - 追加 **`gunicorn==23.0.0`**（生产依赖；本机开发 venv 原先未装）。
  - [`.github/workflows/deploy.yml`](../../.github/workflows/deploy.yml)：`pip install -r requirements.txt -i 清华镜像`，不再旁路装未钉版本的 gunicorn。
  - DEPLOY 注明依赖版本以仓库 `requirements.txt` 为准。
- **不做**
  - pip-tools / Poetry / 单独 lock 文件。
  - 自动 CVE 扫描 CI（仍建议定期人工关注 `python-docx` / `lxml` 等）。

## 决策（用户确认）

1. 直接钉 `requirements.txt`（不用 pip-tools）。
2. 直接依赖 + 传递依赖一起钉；gunicorn 写入并钉版本。
3. 版本来源：本机 freeze；gunicorn → `23.0.0`。

## 验收

- `requirements.txt` 无裸 `>=`；含 `gunicorn==23.0.0`。
- deploy 命令与文件一致。

## 落地记录

- 日期：2026-11-20
- 状态：已实现
