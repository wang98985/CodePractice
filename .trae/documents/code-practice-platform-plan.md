# 线上代码练习评测平台实施计划

## Context（背景与目标）

在空工作区从零构建一个线上代码练习评测平台（迷你 OJ / 类 LeetCode）。用户要求：

- 前端 **Vue 3**，后端 **Django**，数据库 **MySQL**
- 用户账号三级角色：**普通用户 / 管理员 / 超级管理员**
- 必须使用**消息队列（MQ）**——用于提交判题任务异步化
- 提供 **AI 助理**辅助解答（OpenAI 兼容 API，SSE 流式，无 key 时优雅降级）

环境约束：Windows 本地开发。关键技术决策：Celery 5 + RabbitMQ 作 MQ（Windows 用 `--pool=solo`）；PyMySQL 代替 mysqlclient（免编译）；判题用 subprocess + psutil 内存采样（Windows 无 `resource.setrlimit`）；AI 走 .env 配置的 OpenAI 兼容端点（DeepSeek/通义/OpenAI 均可）。

---

## 一、目录结构

```
temp_20261010_01/
├── docker-compose.yml          # MySQL 8 + RabbitMQ 3（management）
├── README.md
├── backend/
│   ├── manage.py / requirements.txt / .env.example / pytest.ini
│   ├── config/                 # Django 工程配置
│   │   ├── __init__.py         # pymysql.install_as_MySQLdb() + celery autodiscover
│   │   ├── settings.py / urls.py / celery.py
│   │   └── sandbox/            # 判题临时目录（gitignore，自动创建）
│   └── apps/
│       ├── accounts/           # User(role) + JWT + 权限类 + 管理端用户接口
│       ├── problems/           # Problem / TestCase / Tag + 筛选
│       ├── submissions/        # Submission 状态机 + 提交/轮询接口
│       ├── judge/              # tasks.py(Celery) / languages.py / runner.py / verdicts.py
│       └── assistant/          # ChatSession/ChatMessage + SSE 流式聊天
└── frontend/
    ├── vite.config.js          # dev proxy /api → 127.0.0.1:8000
    └── src/
        ├── api/                # axios 封装（401 自动刷新）+ SSE fetch 客户端
        ├── stores/             # Pinia: auth / assistant
        ├── router/index.js     # 登录守卫 + meta.roles 角色守卫
        ├── layouts/MainLayout.vue
        ├── views/              # auth / problems / submissions / admin(5页) / errors
        ├── components/         # CodeEditor(CodeMirror6) / AssistantChat / VerdictBadge / TestCaseEditor
        └── utils/verdict.js
```

## 二、核心数据模型

| 模型 | 关键字段 |
|---|---|
| **User**（AbstractUser） | `role`(user/admin/super_admin, 默认 user)、email(unique)；`AUTH_USER_MODEL`；createsuperuser 强制 super_admin |
| **Tag** | name(unique)；与 Problem M2M |
| **Problem** | title、description(Markdown)、difficulty(easy/medium/hard)、time_limit_ms(默认2000)、memory_limit_kb(默认65536)、allowed_languages(JSON, 默认["python"])、reference_answer(admin可见)、is_public、created_by |
| **TestCase** | problem FK、input_data、expected_output、is_sample(题面示例)、is_hidden(判题用例)、order |
| **Submission** | user/problem FK、language、code(≤64KB)、status 状态机、time_used_ms、memory_used_kb、passed_cases/total_cases、error_message、created_at/finished_at；索引 (user,-created_at)、(problem,-created_at)、status |
| **ChatSession/ChatMessage** | session(user, problem可空, title)；message(role user/assistant/system, content)；上下文取最近10条 |

**状态机**：`pending → judging → {accepted, wrong_answer, time_limit_exceeded, memory_limit_exceeded, runtime_error, compile_error, system_error}`

## 三、API 端点清单（前缀 /api/）

| 域 | 端点 | 权限 |
|---|---|---|
| 认证 | POST auth/register/ · POST auth/login/(JWT含role) · POST auth/refresh/ · GET/PUT auth/me/ | 公开/登录 |
| 题目 | GET problems/（search/difficulty/tag 筛选分页，仅 is_public）· GET problems/{id}/（裁剪隐藏字段）· GET tags/ | 公开 |
| 题目管理 | POST/PUT/PATCH/DELETE problems/{id}/ · problems/{id}/test-cases/ CRUD · GET admin/problems/（含未公开） | admin |
| 提交 | POST submissions/（入队 MQ 返回 pending）· GET submissions/（我的，admin 可查他人）· GET submissions/{id}/ · GET submissions/{id}/status/（轻量轮询） | 登录 |
| AI 助理 | GET/POST assistant/sessions/ · GET sessions/{id}/messages/ · POST assistant/chat/（**SSE 流式**，自动建会话+消息落库） | 登录 |
| 用户管理 | GET admin/users/ · PATCH admin/users/{id}/（禁用/重置密码） | admin |
| 超管 | PATCH admin/users/{id}/set-role/ · GET/POST admin/admins/ · GET admin/dashboard/（统计+近7天趋势）· GET/PUT admin/settings/ | super_admin |

## 四、判题流程（MQ 核心）

```
前端 POST /submissions → API 校验 → Submission(status=pending) 写 MySQL
  → Celery send_task 入 RabbitMQ → 201 返回
Celery worker(--pool=solo) 消费 → status=judging → 读题目+用例：
  ① py_compile 语法预检 → 失败记 compile_error + stderr
  ② 逐用例 Popen(python main.py, stdin=用例输入)
     - 超时 kill 进程树 → TLE
     - psutil 50ms 采样 RSS 峰值超限 → MLE
     - 非零退出/stderr → RE；stdout 截断 64KB
     - 输出对比(去行尾空白) → WA
  ③ 全部通过 → accepted，回写 time/memory/passed_cases
前端 1~2s 轮询 /status/ 直至终态
兜底：任务重试1次后仍失败 → system_error；管理命令 cleanup_stuck_submissions 清理超10分钟 judging
```

## 五、关键技术要点

1. **Celery on Windows**：必须 `celery -A config worker -l info --pool=solo`；任务只传 submission_id，数据从 DB 读；不用 result backend（结果直接回写 MySQL）；杀进程树用 psutil 递归 kill（Windows 无进程组）
2. **PyMySQL**：`config/__init__.py` 顶部 `pymysql.install_as_MySQLdb()` + 伪造 version_info；`OPTIONS={"charset":"utf8mb4"}`；Celery 任务开头 `close_old_connections()`
3. **JWT**：SimpleJWT，ACCESS 30min/REFRESH 7d，`ROTATE_REFRESH_TOKENS + BLACKLIST_AFTER_ROTATION`；自定义登录响应携带 role；前端 401 自动刷新重放
4. **SSE**：Django `StreamingHttpResponse`（text/event-stream）；上游 `httpx.stream` 调 OpenAI 兼容 `/chat/completions`(stream=True)；事件 `data: {"delta"}` / done / error；AI_API_KEY 为空或调用失败 → 本地规则回复降级（同样流式）；前端 fetch ReadableStream 手写解析
5. **判题安全**：超时 communicate(timeout) + kill 树；内存采样近似限制（注明局限）；输出/代码 64KB 截断；每题临时目录 `config/sandbox/{sid}/` 判完即删；语言注册表预留 C/C++/Java 字段（compile_cmd/run_cmd/source_filename），MVP 只启用 Python
6. **CORS**：开发期 Vite proxy 同源，同时配 `CORS_ALLOWED_ORIGINS` 备直连

## 六、配置文件

- `.env.example`：SECRET_KEY/DEBUG/ALLOWED_HOSTS、DB_*(oj_platform/oj/oj_pass_123)、RABBITMQ_URL(amqp://guest:guest@127.0.0.1:5672//)、CORS_ALLOWED_ORIGINS、AI_API_BASE_URL/AI_API_KEY/AI_MODEL/AI_TIMEOUT_SECONDS
- `docker-compose.yml`：mysql:8.0（utf8mb4、healthcheck、volume）+ rabbitmq:3-management（5672/15672）。若本机未装 Docker，可改用本机 MySQL + RabbitMQ 安装包，仅需改 .env
- `requirements.txt`：Django~=5.0、DRF~=3.15、SimpleJWT~=5.3、cors-headers、celery~=5.3、pymysql+cryptography、python-dotenv、httpx、psutil、django-filter、markdown
- 前端依赖：vue3/vue-router4/pinia/axios/element-plus/markdown-it/dompurify + CodeMirror 6（lang-python/theme-one-dark 等）+ vite5

## 七、实施步骤（按依赖顺序）

1. **基础设施**：docker-compose.yml、backend venv + requirements、前端 Vite 骨架
2. **Django 骨架 + 认证**：config 工程 + PyMySQL 接入 + migrate；自定义 User(role)（**必须最先定稿再做其他迁移**）；JWT 登录/注册/me；IsAdminRole/IsSuperAdminRole 权限类
3. **题目模块**：Tag/Problem/TestCase 模型；公开列表/详情（筛选+裁剪）；admin CRUD + 用例 CRUD
4. **MQ + 判题引擎（核心）**：celery.py + ping 任务验证；judge(verdicts→languages→runner→tasks.run_submission)；submissions 入队/列表/轮询；用 AC/WA/TLE(死循环)/CE(语法错误)/RE/MLE 样例逐个验证；cleanup_stuck 命令
5. **AI 助理**：会话/消息模型 + 接口；httpx 流式 + 降级；SSE 视图 curl 联调；上下文注入
6. **前端**：axios+守卫 → 登录/注册 → 题目列表/详情 → 编辑器+提交+轮询 → 提交记录 → 管理端5页（按角色显隐菜单）→ AssistantChat 悬浮窗
7. **收尾**：seed_demo 管理命令（3~5 道示例题含用例标签）；README 启动手册

## 八、端到端验收

1. `docker compose up -d` → MySQL/RabbitMQ 就绪（15672 管理台可登录）
2. `cp .env.example .env` → `migrate` → `seed_demo` → `createsuperuser`
3. 终端 A：`runserver 0.0.0.0:8000`；终端 B：`celery -A config worker -l info --pool=solo`；前端 `npm run dev` → localhost:5173
4. 功能走查：注册普通用户 → 筛选题目 → 提交正确代码得 AC（耗时/内存有值）→ 死循环得 TLE → 语法错误得 CE → 我的提交可见历史 → AI 悬浮窗流式回复（清空 key 验证降级）→ admin 管理题目/用户（无管理员管理菜单）→ super_admin 可见仪表盘+提权
5. 异常兜底：停 worker 提交留 pending → 重启被消费；运行 cleanup_stuck_submissions

**风险**：首迁移前必须定稿 User；Windows 防火墙放行 Python/MySQL；dev server 单线程，SSE 并发有限（README 注明生产用 gunicorn+gevent）

## 关键文件

- backend/config/settings.py（配置中枢）
- backend/config/celery.py（MQ 入口）
- backend/apps/judge/runner.py（判题沙箱核心）
- backend/apps/submissions/models.py（状态机落库）
- backend/apps/assistant/views.py（SSE + 降级）
