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
#   1. Python3、python3-venv、Nginx、gunicorn、systemd
#      pip 已配置使用清华镜像 https://pypi.tuna.tsinghua.edu.cn/simple
#   2. 安全组放行 22
#   3. 无密 sudo 重启 word-retrieval：
#
#      ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl restart word-retrieval, /bin/systemctl status word-retrieval, /bin/systemctl is-active word-retrieval
#
#   4. 已创建 word-retrieval.service。会话/下载在磁盘 `.cache/`，可用多 worker。
#      ExecStart 示例（按实际 User、WorkingDirectory、venv 路径改）。
#      优雅停机（SECURITY 3.1）：TimeoutStopSec / KillMode + gunicorn
#      --graceful-timeout / --timeout；改完后须手动：
#        sudo systemctl daemon-reload && sudo systemctl restart word-retrieval
#      Actions 不会改 unit 文件。
#
#      [Service]
#      User=deploy
#      WorkingDirectory=/home/deploy/Word-Retrieval
#      TimeoutStopSec=60
#      KillMode=mixed
#      ExecStart=/home/deploy/Word-Retrieval/.venv/bin/gunicorn \
#        -w 2 -b 127.0.0.1:5000 \
#        --timeout 120 \
#        --graceful-timeout 30 \
#        'word_retrieval:create_app()'
#      Restart=on-failure
#
#      说明：--graceful-timeout 30 = 停 worker 最多等 30s；
#      TimeoutStopSec=60 给 master 留余量；--timeout 120 = 单请求硬上限
#      （上传/派生勿误杀）。探活：curl -s http://127.0.0.1:5000/healthz
#
#      应用日志（SECURITY 3.2）：Flask 打 JSON 一行到 stderr（含 request_id；
#      响应头 X-Request-ID）。查看：journalctl -u word-retrieval -f
#      GET /healthz 不打应用 INFO 访问行。
#
# 五、关于 ecdict.db（服务器若也无法访问 GitHub）：
#
#   在能上网的电脑上：
#     python build_ecdict_db.py
#   然后把 dictionaries/ecdict.db 上传到服务器：
#     scp dictionaries/ecdict.db USER@IP:~/Word-Retrieval/dictionaries/
#
# 六、触发：push 任意分支（含 main / feature/* 等），或 Actions 页手动 Run workflow
#     注意：任意分支都会覆盖服务器上同一份部署目录，推实验分支也会上线。
#
# 七、HTTPS（Nginx + Let's Encrypt；在服务器上手动做一次，勿写进每次 Actions）
#
#   前置：域名 A 记录已指向本机；安全组已放行 TCP 80 与 443；gunicorn 仍只听 127.0.0.1:5000。
#   不要对公网开放 5000。
#
#   1. 安全组入方向增加：TCP 443/443，0.0.0.0/0。
#
#   2. 安装 certbot（Ubuntu 22.04 示例）：
#        sudo apt update
#        sudo apt install -y certbot python3-certbot-nginx
#
#   3. 先保证 HTTP 反代可用（示例 /etc/nginx/sites-available/wordsorting）：
#
#        # 限流区：放在 http {} 块（如 nginx.conf）或本文件外层；按 IP
#        # limit_req_zone $binary_remote_addr zone=wr_general:10m rate=10r/s;
#        # limit_req_zone $binary_remote_addr zone=wr_heavy:10m rate=2r/s;
#
#        # upstream + 短连重试（SECURITY 3.1）：单机一个后端时，
#        # proxy_next_upstream 主要是「再试同机一次」，对进程完全未起来
#        # 帮助有限；真正缩短 refused 靠 gunicorn 尽快 bind + 优雅停。
#        # 须服务器手动改；Actions 不改 Nginx。
#        upstream word_retrieval {
#            server 127.0.0.1:5000;
#            keepalive 8;
#        }
#
#        server {
#            listen 80;
#            server_name wordsorting.com;
#
#            client_max_body_size 16m;
#
#            location = /upload {
#                limit_req zone=wr_heavy burst=5 nodelay;
#                proxy_pass http://word_retrieval;
#                proxy_http_version 1.1;
#                proxy_set_header Connection "";
#                proxy_connect_timeout 2s;
#                proxy_read_timeout 120s;
#                proxy_next_upstream error timeout http_502 http_503;
#                proxy_next_upstream_tries 2;
#                proxy_set_header Host $host;
#                proxy_set_header X-Real-IP $remote_addr;
#                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
#                proxy_set_header X-Forwarded-Proto $scheme;
#            }
#
#            location = /api/parse_wordlist {
#                limit_req zone=wr_heavy burst=5 nodelay;
#                proxy_pass http://word_retrieval;
#                proxy_http_version 1.1;
#                proxy_set_header Connection "";
#                proxy_connect_timeout 2s;
#                proxy_read_timeout 120s;
#                proxy_next_upstream error timeout http_502 http_503;
#                proxy_next_upstream_tries 2;
#                proxy_set_header Host $host;
#                proxy_set_header X-Real-IP $remote_addr;
#                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
#                proxy_set_header X-Forwarded-Proto $scheme;
#            }
#
#            location / {
#                limit_req zone=wr_general burst=20 nodelay;
#                proxy_pass http://word_retrieval;
#                proxy_http_version 1.1;
#                proxy_set_header Connection "";
#                proxy_connect_timeout 2s;
#                proxy_read_timeout 120s;
#                proxy_next_upstream error timeout http_502 http_503;
#                proxy_next_upstream_tries 2;
#                proxy_set_header Host $host;
#                proxy_set_header X-Real-IP $remote_addr;
#                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
#                proxy_set_header X-Forwarded-Proto $scheme;
#            }
#        }
#
#      限流与 upstream 重试为可选加固：须在服务器上手动写入、
#      sudo nginx -t && sudo systemctl reload nginx。Actions 部署不会改 Nginx。
#      健康检查可用：curl -s http://127.0.0.1:5000/healthz（轻量，不加载 ECDICT）
#
#      sudo ln -sf /etc/nginx/sites-available/wordsorting /etc/nginx/sites-enabled/
#      sudo nginx -t && sudo systemctl reload nginx
#
#   4. 申请证书并让 certbot 改写 Nginx（仅裸域；若有 www 解析再加 -d www.wordsorting.com）：
#        sudo certbot --nginx -d wordsorting.com
#
#      成功后应出现 listen 443 ssl，且 80 端口 HTTP→HTTPS 重定向（certbot 通常自动加）。
#      若需手写 80 跳转：
#        return 301 https://$host$request_uri;
#
#   5. 验收：
#        curl -I http://wordsorting.com          # 期望 301 → https
#        curl -I https://wordsorting.com         # 期望 200
#        curl -I http://127.0.0.1:5000           # 本机仍通；公网勿放行 5000
#
#   证书续期：certbot 定时任务一般已装好；可测：sudo certbot renew --dry-run
#