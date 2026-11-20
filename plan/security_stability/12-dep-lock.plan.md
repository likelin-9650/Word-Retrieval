---
name: 依赖锁定 3.5
overview: 落地 SECURITY 3.5：requirements.txt 以本机 venv freeze 全量 == 钉死（含传递依赖）+ gunicorn==23.0.0；deploy.yml 只 pip install -r requirements.txt。
todos:
  - id: pin-requirements
    content: requirements.txt 钉死 + gunicorn；deploy.yml 去掉旁路 gunicorn
    status: completed
  - id: docs-35
    content: 12 方案、SECURITY §3.5、HANDOFF、DEPLOY、README
    status: completed
isProject: false
---

# 3.5 依赖锁定

## 范围

- **做**：`requirements.txt` 全部 `==`；本机 freeze 直接+传递依赖 + `gunicorn==23.0.0`；Actions 只装该文件。
- **不做**：pip-tools / Poetry；CVE 自动扫描流水线（文档提醒定期人工看即可）。

## 决策（用户确认）

1. 形式 **A**：直接钉 `requirements.txt`。
2. 一起钉传递依赖；gunicorn 写入并钉版本。
3. 版本以本机 venv 为准；gunicorn 本机无 → **23.0.0**。
