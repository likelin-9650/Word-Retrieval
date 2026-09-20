# ═══════════════════════════════════════════
# GitHub Actions 自动部署说明（配合 .github/workflows/deploy.yml）
# ═══════════════════════════════════════════

# 一、在 GitHub 仓库 Settings → Secrets and variables → Actions 中添加：
#
#   SERVER_IP        服务器公网 IP 或域名
#   SERVER_USER      SSH 登录用户名（如 ubuntu、root，需与私钥匹配）
#   SSH_PRIVATE_KEY  整段私钥（含 -----BEGIN ... PRIVATE KEY-----）
#   DEPLOY_PATH      （可选）服务器上项目绝对路径
#                    不填则默认：/home/<SERVER_USER>/Word-Retrieval
#                    若你克隆在 /var/www/Word-Retrieval，请填该路径
#
# 二、服务器准备：
#   1. 已按部署教程安装 Python、venv、Nginx、gunicorn、systemd
#   2. 已 git clone 本仓库到 DEPLOY_PATH
#   3. 公钥已写入该用户 ~/.ssh/authorized_keys
#   4. 安全组放行 22 端口给外网（或至少 GitHub Actions IP；初学可先全放 22）
#   5. 部署用户可无密 sudo 重启服务，例如：
#
#      sudo visudo
#      # 追加一行（把 ubuntu 换成你的 SERVER_USER）：
#      ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl restart word-retrieval, /bin/systemctl status word-retrieval, /bin/systemctl is-active word-retrieval
#
#   6. systemd 服务名必须是 word-retrieval（与 deploy.yml 一致）
#
# 三、私钥注意：
#   - 用专用部署密钥，不要用你唯一的个人主密钥（可另生成一对）
#   - ssh-keygen -t ed25519 -C "github-deploy" -f ./github_deploy
#   - 公钥 → 服务器 authorized_keys；私钥全文 → GitHub Secret SSH_PRIVATE_KEY
#
# 四、触发：
#   - push 到 main，或在 Actions 页手动 Run workflow
#
# 五、本项目不会：
#   - 每次部署重建 ecdict.db（仅文件缺失时构建）
#   - 使用 npm / pm2（那是 Node 项目的做法）
