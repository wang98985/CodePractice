# Vercel 部署指南

本项目已适配 Vercel 部署：**前端静态托管 + 后端 Python Serverless**。

> ⚠️ Vercel Serverless 限制：判题改为**同步执行**（无 Celery worker），单次判题需在 60 秒内完成。

## 一、推送代码到 GitHub

```bash
cd 项目目录
git remote add origin https://github.com/wang98985/CodePractice.git
git push -u origin main
```

> 如果连接超时，需要配置 git 代理或使用 GitHub Desktop。

## 二、准备外部 MySQL 数据库

Vercel 不提供 MySQL，需使用云数据库（任选其一）：

| 服务 | 免费额度 | 说明 |
|---|---|---|
| [PlanetScale](https://planetscale.com) | 5GB | 推荐，兼容 MySQL |
| [Aiven MySQL](https://aiven.io) | 1 个月免费 | |
| 阿里云 RDS | 按量付费 | 国内访问快 |

创建数据库后，记录以下信息：
- 主机地址（DB_HOST）
- 端口（DB_PORT，通常 3306）
- 数据库名（DB_NAME）
- 用户名（DB_USER）
- 密码（DB_PASSWORD）

## 三、部署后端（Vercel）

1. 登录 [Vercel](https://vercel.com) → **Add New** → **Project**
2. 导入 GitHub 仓库 `CodePractice`
3. **Framework Preset** 选 **Other**
4. **Root Directory** 设为 `backend`
5. **Build Command** 留空
6. **Output Directory** 留空
7. 在 **Environment Variables** 中添加：

| 变量名 | 值 | 说明 |
|---|---|---|
| `SECRET_KEY` | 随机长字符串 | Django 密钥，务必修改 |
| `DEBUG` | `False` | 关闭调试 |
| `ALLOWED_HOSTS` | `.vercel.app` | 允许 Vercel 域名 |
| `DB_NAME` | 你的数据库名 | |
| `DB_USER` | 数据库用户名 | |
| `DB_PASSWORD` | 数据库密码 | |
| `DB_HOST` | 数据库主机地址 | |
| `DB_PORT` | `3306` | |
| `SYNC_JUDGE` | `true` | 同步判题（Vercel 必须） |
| `SANDBOX_DIR` | `/tmp/oj_sandbox` | 沙箱目录（Vercel 只读 FS） |
| `EMAIL_HOST_USER` | `1606383294@qq.com` | 发件邮箱 |
| `EMAIL_HOST_PASSWORD` | QQ 邮箱 SMTP 授权码 | 留空则验证码打印日志 |
| `CORS_ALLOWED_ORIGINS` | 前端 Vercel 域名 | 如 `https://codepractice-frontend.vercel.app` |

8. 点击 **Deploy**

## 四、初始化后端数据库

部署成功后，在 Vercel 项目中进入 **Settings → Functions**，或使用 Vercel CLI 执行迁移：

```bash
# 安装 Vercel CLI
npm i -g vercel

# 进入后端目录并执行迁移
cd backend
vercel --prod
vercel exec python manage.py migrate
vercel exec python manage.py createsuperuser
vercel exec python manage.py seed_demo
```

> 如果 `vercel exec` 不可用，可临时在本地连远程数据库执行迁移（修改本地 `.env` 指向云数据库）。

## 五、部署前端（Vercel）

1. **Add New** → **Project** → 导入同一仓库 `CodePractice`
2. **Framework Preset** 选 **Vite**
3. **Root Directory** 设为 `frontend`
4. **Build Command**：`npm run build`
5. **Output Directory**：`dist`
6. 添加环境变量：

| 变量名 | 值 | 说明 |
|---|---|---|
| `VITE_API_BASE_URL` | 后端 Vercel 域名 + `/api` | 如 `https://codepractice-backend.vercel.app/api` |

7. 点击 **Deploy**

## 六、验证部署

1. 访问前端域名 → 注册账号（需 QQ 邮箱验证码）
2. 登录 → 查看题目列表
3. 提交代码 → 验证判题功能
4. 用超管账号登录 → 批量导入 1000 道题（`problems_1000.csv`）

## 环境变量速查

### 后端

```
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=.vercel.app
DB_NAME=oj_platform
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=your_db_host
DB_PORT=3306
SYNC_JUDGE=true
SANDBOX_DIR=/tmp/oj_sandbox
EMAIL_HOST_USER=1606383294@qq.com
EMAIL_HOST_PASSWORD=qq_smtp_auth_code
CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app
```

### 前端

```
VITE_API_BASE_URL=https://your-backend.vercel.app/api
```

## 已知限制

1. **判题超时**：Vercel Serverless 最长 60 秒，复杂题目可能超时
2. **无 Celery**：判题同步执行，高并发时性能受限
3. **文件系统只读**：沙箱仅能写 `/tmp`，每次请求后不保留
4. **AI 助理**：SSE 流式响应可能受 Vercel 超时限制，无 API key 时降级本地回复

## 本地开发 vs Vercel

| 功能 | 本地开发 | Vercel 生产 |
|---|---|---|
| 判题模式 | Celery 异步 | 同步（SYNC_JUDGE=true） |
| 沙箱目录 | `backend/config/sandbox/` | `/tmp/oj_sandbox` |
| MQ Broker | Redis / RabbitMQ | 不需要 |
| 邮件 | 控制台打印 / SMTP | 需配置 SMTP 授权码 |
