# ═══════════════════════════════════════════
# GitHub Actions 自动部署说明（配合 .github/workflows/deploy.yml）
# 登录方式：SSH 用户名 + 私钥
# ═══════════════════════════════════════════

# 一、工作流如何部署（重要）
#
#   GitHub Runner 上 checkout 代码 → 打包 → SCP 传到服务器 → 解压 → pip → 重启服务
#   服务器不再执行 git clone / git pull，因此即使服务器访问不了 github.com:443 也能部署。
#
# 二、在 GitHub 仓库 Settings → Secrets and variables → Actions 中添加：
#
#   SERVER_IP         服务器公网 IP 或域名
#   SERVER_USER       SSH 登录用户名（如 ubuntu、root，需与私钥匹配）
#   SSH_PRIVATE_KEY   整段私钥（必须含 BEGIN/END 头尾）
#   DEPLOY_PATH       （可选）服务器上项目绝对路径
#                     不填则默认：$HOME/Word-Retrieval
#
# 三、生成专用部署密钥（推荐在本机执行）：
#
#   ssh-keygen -t ed25519 -C "github-deploy" -f ./github_deploy -N ""
#   # 公钥写入服务器 ~/.ssh/authorized_keys
#   # 私钥全文 → GitHub Secret SSH_PRIVATE_KEY
#   # 本机测通：ssh -i ./github_deploy USER@IP
#
# 四、服务器准备：
#   1. Python3、python3-venv、git（可选）、Nginx、gunicorn、systemd
#   2. 安全组放行 22
#   3. 无密 sudo 重启 word-retrieval：
#
#      ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl restart word-retrieval, /bin/systemctl status word-retrieval, /bin/systemctl is-active word-retrieval
#
#   4. 已创建 word-retrieval.service
#
# 五、关于 ecdict.db（服务器若也无法访问 GitHub）：
#
#   在能上网的电脑上：
#     python build_ecdict_db.py
#   然后把 dictionaries/ecdict.db 上传到服务器：
#     scp dictionaries/ecdict.db USER@IP:~/Word-Retrieval/dictionaries/
#
# 六、触发：push 到 main，或 Actions 页手动 Run workflow
