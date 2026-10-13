# 云服务器部署指南（Docker Compose）

面向本机开发以外的正式部署：一台 Ubuntu 云服务器 + Docker Compose，一次性拉起 MySQL、Redis、Django、Celery 判题 worker、Nginx 五个服务。

## 架构

```
用户浏览器
    │  :80
    ▼
 Nginx（oj-web 容器）
    ├── /            前端静态文件（Vue 构建产物）
    ├── /api/  ────► Django（oj-backend 容器，Gunicorn）
    ├── /admin/ ───► Django 自带后台
    └── /static/ ──► Django 静态资源（WhiteNoise）
                         │
                         ├── MySQL 8（oj-mysql 容器）
                         └── Redis（oj-redis 容器）— MQ broker
                                  │
                                  ▼
                            Celery 判题 worker（oj-worker 容器）
```

判题链路：提交代码 → 写入 MySQL（pending）→ 投递任务到 Redis 队列 → worker 取任务 → 沙箱执行对作用例 → 结果回写 MySQL（accepted / wrong_answer / TLE / MLE / RE / CE）。

> 前端不注入 `VITE_API_BASE_URL`，默认请求相对路径 `/api`，由 Nginx 反代到后端，**前后端同域，无跨域问题**。

## 一、准备服务器

- 系统：Ubuntu 22.04 / 24.04 / 26.04（其他 Debian 系同理）
- 配置：1 核 2G 起（判题要起 Python 子进程，内存越大越稳）
- 磁盘：≥ 20G（MySQL 镜像约 1.1G，数据另算）
- 安全组：放行 **22**（SSH）和 **80**（HTTP）；有域名并要上 HTTPS 时再放行 **443**

## 二、安装 Docker

```bash
apt-get update
apt-get install -y docker.io docker-compose-v2
systemctl enable --now docker
docker --version && docker compose version
```

国内服务器访问不了 Docker Hub，需配置镜像加速：

```bash
mkdir -p /etc/docker
cat > /etc/docker/daemon.json <<'JSON'
{
  "registry-mirrors": ["https://docker.m.daocloud.io", "https://docker.1ms.run"],
  "log-driver": "json-file",
  "log-opts": {"max-size": "10m", "max-file": "3"}
}
JSON
systemctl restart docker
```

内存 ≤ 2G 时建议加 2G swap，避免构建/判题时 OOM：

```bash
fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

## 三、上传代码

在服务器上准备目录并解压源码（本地打包时已排除 `venv`、`node_modules`、`__pycache__`）：

```bash
mkdir -p /opt/codepractice
tar xzf oj_src.tar.gz -C /opt/codepractice
cd /opt/codepractice
```

## 四、配置环境变量

```bash
cd deploy
cp .env.prod.example .env.prod
vi .env.prod
```

必须修改的项：

| 变量 | 说明 |
|---|---|
| `SECRET_KEY` | Django 密钥，填一长串随机字符 |
| `ALLOWED_HOSTS` | 公网 IP 或域名，逗号分隔 |
| `CSRF_TRUSTED_ORIGINS` | 形如 `http://你的IP`（用域名+HTTPS 就写 `https://域名`） |
| `DB_PASSWORD` / `MYSQL_ROOT_PASSWORD` | 数据库密码，自行生成 |
| `CORS_ALLOWED_ORIGINS` | 同域反代可留空 |
| `EMAIL_HOST_PASSWORD` | QQ 邮箱 SMTP 授权码（注册验证码用），留空则验证码打印到容器日志 |

> `.env.prod` 已加入 `.gitignore`，不会误提交。

## 五、启动

```bash
cd /opt/codepractice/deploy
./deploy.sh up          # 构建镜像 + 启动全部服务（首次约 3-10 分钟）
./deploy.sh ps          # 五个容器应为 running / healthy
```

首次构建会从 `registry.npmmirror.com` 装前端依赖、从清华 PyPI 镜像装后端依赖，无需翻墙。

初始化数据库与账号：

```bash
./deploy.sh migrate     # 建表
./deploy.sh collect     # 收集 Django 后台静态文件
./deploy.sh superuser   # 创建超级管理员：admin / admin123456
./deploy.sh shell       # 需要的话进 Django shell
```

导入示例题目（4 道）：

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod \
  exec -T backend python manage.py seed_demo
```

浏览器打开 `http://服务器IP` 即可访问；用超管账号登录后，可在「题目管理 → 批量导入」上传 `problems_1000.csv` 批量导入题目。

## 六、日常运维

```bash
./deploy.sh logs            # 全部日志
./deploy.sh logs worker     # 只看判题 worker
./deploy.sh restart         # 重启
./deploy.sh down            # 停止（保留数据卷）
```

更新代码：重新上传解压后执行 `./deploy.sh up`（会重建镜像；数据卷不受影响）。

## 七、常见问题

**外网打不开，容器却是 running**
安全组没放行 80 端口，去云控制台加规则。

**`docker pull` 超时**
镜像加速没生效，检查 `/etc/docker/daemon.json` 后 `systemctl restart docker`。

**worker 一直重启 / 判题卡在 pending**
Redis 未就绪或 broker 地址不对，`./deploy.sh logs worker` 看报错。

**判题全部 system_error**
判题沙箱需要写临时目录，检查 worker 容器的 `/tmp` 是否可写（compose 已配置 `tmpfs: /tmp`）。

**AI 助理没有真实回答**
`.env.prod` 里 `AI_API_KEY` 为空时会走本地规则降级回复，填入 OpenAI 兼容服务的 Key 即可（如 DeepSeek）。

**数据库时区**
MySQL 容器已设 `TZ=Asia/Shanghai`，Django 侧 `TIME_ZONE` 亦为 `Asia/Shanghai`。

## 八、安全提示

- 目前仅监听 80（HTTP）。若要 HTTPS，建议在宿主机装 Nginx 或 Caddy 做 TLS 终止，转发到 `127.0.0.1:80`。
- MySQL 未映射到宿主机端口，仅容器内网可达；Redis 同理。
- 判题沙箱为进程级隔离（超时杀进程树 + 内存采样），非内核级沙箱。若对外开放，建议限制注册或改为专用判题机。