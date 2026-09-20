# ═══════════════════════════════════════════
# GitHub Actions 自动部署说明（配合 .github/workflows/deploy.yml）
# 登录方式：SSH 用户名 + 密码（不再使用私钥）
# ═══════════════════════════════════════════

# 一、在 GitHub 仓库 Settings → Secrets and variables → Actions 中添加：
#
#   SERVER_IP        服务器公网 IP 或域名
#   SERVER_USER      SSH 登录用户名（如 ubuntu、root）
#   SERVER_PASSWORD  该用户的登录密码
#   DEPLOY_PATH      （可选）服务器上项目绝对路径
#                    不填则默认：/home/<SERVER_USER>/Word-Retrieval
#                    若你克隆在 /var/www/Word-Retrieval，请填该路径
#
#   可删除旧的 SSH_PRIVATE_KEY（若已不用密钥登录）。
#
# 二、服务器必须允许密码登录 SSH（很多云镜像默认只允许密钥）：
#
#   sudo nano /etc/ssh/sshd_config
#   # 确认或修改为：
#   PasswordAuthentication yes
#   # 若用 root 登录，还需视情况：
#   # PermitRootLogin yes
#   # 或 PermitRootLogin prohibit-password 改为 yes（仅在你明确需要时）
#
#   sudo systemctl restart ssh   # 部分系统服务名是 sshd
#
#   用本机先测通：
#   ssh SERVER_USER@SERVER_IP
#   # 能输入密码登录后再跑 Actions
#
# 三、服务器其它准备：
#   1. 已安装 Python3、python3-venv、git、（生产）Nginx / gunicorn / systemd
#   2. 项目目录可不预先存在：工作流会在默认路径自动 git clone
#      若代码已放在别处，请设置 Secret DEPLOY_PATH 为实际绝对路径
#   3. 安全组放行 22 端口
#   4. 部署用户可无密 sudo 重启服务，例如：
#
#      sudo visudo
#      # 追加一行（把 ubuntu 换成你的 SERVER_USER）：
#      ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl restart word-retrieval, /bin/systemctl status word-retrieval, /bin/systemctl is-active word-retrieval
#
#   5. systemd 服务名必须是 word-retrieval（与 deploy.yml 一致）
#      首次 clone 后若还没有该服务，部署会在依赖装完后失败并提示；
#      请先按部署教程建好 word-retrieval.service 再重新 Run workflow
#
# 四、安全提醒：
#   - 密码存在 GitHub Secrets 中相对安全，但不如密钥登录稳妥
#   - 请使用强密码；不要把密码写进仓库代码
#   - 若密码含特殊字符，一般无需转义，整段粘贴到 Secret 即可
#
# 五、触发：
#   - push 到 main，或在 Actions 页手动 Run workflow
#
# 六、本项目不会：
#   - 每次部署重建 ecdict.db（仅文件缺失时构建）
#   - 使用 npm / pm2
