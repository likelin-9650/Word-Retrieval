# ═══════════════════════════════════════════
# GitHub Actions 自动部署说明（配合 .github/workflows/deploy.yml）
# 登录方式：SSH 用户名 + 私钥
# ═══════════════════════════════════════════

# 一、在 GitHub 仓库 Settings → Secrets and variables → Actions 中添加：
#
#   SERVER_IP         服务器公网 IP 或域名
#   SERVER_USER       SSH 登录用户名（如 ubuntu、root，需与私钥匹配）
#   SSH_PRIVATE_KEY   整段私钥（必须含头尾）：
#                     -----BEGIN OPENSSH PRIVATE KEY-----
#                     ……
#                     -----END OPENSSH PRIVATE KEY-----
#   DEPLOY_PATH       （可选）服务器上项目绝对路径
#                     不填则默认：$HOME/Word-Retrieval
#
#   可删除不再使用的 SERVER_PASSWORD。
#
# 二、生成专用部署密钥（推荐在本机执行）：
#
#   ssh-keygen -t ed25519 -C "github-deploy" -f ./github_deploy -N ""
#   # 得到：github_deploy（私钥）、github_deploy.pub（公钥）
#
#   # 公钥追加到服务器（把 USER、IP 换成你的）：
#   type github_deploy.pub | ssh USER@IP "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
#   # 或登录服务器后手动把 .pub 内容追加进 ~/.ssh/authorized_keys
#
#   # 私钥全文粘贴到 GitHub Secret：SSH_PRIVATE_KEY
#
#   # 本机先测通：
#   ssh -i ./github_deploy USER@IP
#
# 三、服务器其它准备：
#   1. 已安装 Python3、python3-venv、git、（生产）Nginx / gunicorn / systemd
#   2. 项目目录可不预先存在：工作流会在默认路径自动 git clone
#      若代码在别处，请设置 DEPLOY_PATH
#   3. 安全组放行 22 端口
#   4. 部署用户可无密 sudo 重启服务，例如：
#
#      sudo visudo
#      # 追加一行（把 ubuntu 换成你的 SERVER_USER）：
#      ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl restart word-retrieval, /bin/systemctl status word-retrieval, /bin/systemctl is-active word-retrieval
#
#   5. systemd 服务名必须是 word-retrieval
#      若服务尚未创建，部署会在依赖装完后提示失败
#
# 四、触发：
#   - push 到 main，或在 Actions 页手动 Run workflow
#
# 五、本项目不会：
#   - 每次部署重建 ecdict.db（仅文件缺失时构建）
#   - 使用 npm / pm2
