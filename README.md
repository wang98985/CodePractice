# CodePractice - 在线代码练习评测平台

类 LeetCode 的在线判题（OJ）平台。前端 Vue 3，后端 Django 5 + DRF，数据库 MySQL 8，消息队列 Celery 5（Redis / RabbitMQ 二选一），内置 AI 助理（OpenAI 兼容接口，支持 DeepSeek/通义/OpenAI 等）。

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Vue 3 + Vite 5 + Element Plus + Pinia + Vue Router + CodeMirror 6 |
| 后端 | Django 5 + Django REST Framework + SimpleJWT (JWT) |
| 数据库 | MySQL 8（PyMySQL 驱动，utf8mb4） |
| 消息队列 | Celery 5 + Redis / RabbitMQ（判题任务异步化，Windows 用 `--pool=solo`） |
| AI 助理 | OpenAI 兼容 API（SSE 流式，无 key 时自动降级为本地规则回复） |
| 判题引擎 | subprocess 沙箱（超时 kill 进程树 + psutil 内存采样 + 输出截断），语言注册表可扩展 |

## 用户角色（三级）

| 角色 | 权限 |
|---|---|
| 普通用户 `user` | 练习题目、提交代码、查看自己的提交、AI 助理 |
| 管理员 `admin` | 以上 + 题目/测试用例管理、查看全部提交、用户管理（禁用/重置密码） |
| 超级管理员 `super_admin` | 以上 + 管理员管理、角色调整、系统仪表盘 |

## 目录结构

```
├── docker-compose.yml        # MySQL + RabbitMQ（有 Docker 时一键启动）
├── scripts/init_db.sql       # 建库建用户脚本（本机 MySQL 直接执行）
├── backend/                  # Django 后端
│   ├── config/               # 工程配置（settings/celery/urls）
│   ├── apps/accounts/        # 用户/角色/JWT/管理端用户接口
│   ├── apps/problems/        # 题目/标签/测试用例 + seed_demo 种子数据
│   ├── apps/submissions/     # 提交记录 + 状态机
│   ├── apps/judge/           # 判题引擎（runner 沙箱 / 语言注册表 / Celery 任务）
│   └── apps/assistant/       # AI 助理（SSE 流式 + 会话历史 + 降级）
└── frontend/                 # Vue 3 前端
    └── src/                  # 页面/组件/api/store/路由
```

## 启动步骤（Windows 本机）

### 1. 准备 MySQL

本机已安装 MySQL 8（3306 端口）。用 root 执行初始化脚本（密码替换为你的 root 密码）：

```powershell
& "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -uroot -p < scripts\init_db.sql
```

若不想用 `oj/oj_pass_123` 账号，可改用 root，同时修改 `backend/.env` 中 `DB_USER/DB_PASSWORD`。

> 有 Docker 的机器也可以直接 `docker compose up -d`（自动建库建账号）。

### 2. 启动 MQ Broker（Redis / RabbitMQ 二选一）

后端优先读取 `backend/.env` 中的 `CELERY_BROKER_URL`；未配置时回退 `RABBITMQ_URL`。

**方式 A：Redis（推荐，免安装 Erlang）**

- 直接运行便携版 Redis（项目开发使用的正是这种方式）：

```powershell
& "C:\你的路径\redis\redis-server.exe" --port 6379
```

- 或安装 Memurai / 用 Docker：`docker run -d --name oj-redis -p 6379:6379 redis:7`；
- `.env` 中配置：`CELERY_BROKER_URL=redis://127.0.0.1:6379/0`。

**方式 B：RabbitMQ**

- 下载安装 [RabbitMQ](https://www.rabbitmq.com/install-windows.html)（需先装 Erlang），服务默认监听 `5672`，管理台 `http://localhost:15672`（guest/guest）；
- 或用 Docker：`docker run -d --name oj-rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management`；
- `.env` 中删除 `CELERY_BROKER_URL`（或改为 `amqp://guest:guest@127.0.0.1:5672//`）即可切回。

### 3. 后端

```powershell
cd backend
# 首次：创建虚拟环境并安装依赖（已装可跳过）
python -m venv venv
.\venv\Scripts\pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 确认 backend\.env 中数据库/RabbitMQ/AI 配置正确，然后：
.\venv\Scripts\python manage.py migrate
.\venv\Scripts\python manage.py seed_demo          # 导入 4 道示例题
.\venv\Scripts\python manage.py createsuperuser    # 超级管理员
.\venv\Scripts\python manage.py runserver 0.0.0.0:8000
```

### 4. Celery 判题 worker（另开一个终端）

```powershell
cd backend
.\venv\Scripts\celery -A config worker -l info --pool=solo
```

> Windows 必须加 `--pool=solo`。

### 5. 前端

```powershell
cd frontend
npm install      # 首次
npm run dev      # http://localhost:5173
```

### 6. AI 助理（可选）

编辑 `backend/.env`：

```
AI_API_BASE_URL=https://api.deepseek.com/v1   # 或其他 OpenAI 兼容地址
AI_API_KEY=sk-xxx
AI_MODEL=deepseek-chat
```

不配置 key 时 AI 助理自动降级为本地规则回复（前端体验一致）。

## 验收走查

1. 注册普通用户 → 登录 → 题库看到 4 道种子题 → 筛选难度/标签生效；
2. 打开「A+B 问题」→ 提交正确代码 → 数秒内轮询到 **通过**（耗时/内存有值）；
3. 提交 `while True: pass` → **超时**；语法错误 → **编译错误**（有报错摘要）；
4. 「判断质数」提交 $O(n)$ 暴力 → **超时**（卡暴力题）；「区间求和」同理；
5. 右下角 AI 悬浮窗：带题目上下文提问 → 流式回复；
6. admin 登录：题目管理（含测试用例抽屉）、用户管理，但无「管理员管理」菜单；
7. super_admin 登录：仪表盘（统计/状态分布/7 天趋势）、管理员管理、可将用户提权。

## 运维命令

```powershell
# 清理僵尸提交（judging 超过 10 分钟）
.\venv\Scripts\python manage.py cleanup_stuck_submissions
```

## 已知局限（MVP）

- 判题沙箱为同机 subprocess 隔离（超时/内存/输出限制），无 cgroup/namespace 与网络封锁，适合教学与内网场景；生产建议 Docker/Firecracker 沙箱；
- 内存限制为 psutil 50ms 采样近似值；
- Django dev server 为单线程，SSE 并发有限；生产部署建议 gunicorn+gevent 或 Daphne，并配置 Nginx 对 `/api/assistant/chat/` 关闭缓冲。
