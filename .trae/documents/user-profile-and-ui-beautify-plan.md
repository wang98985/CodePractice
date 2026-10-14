# 用户主页 + 全站界面美化 实施方案

## Context（为什么做）

平台已上线（`http://101.37.70.252`，Docker Compose 五容器），核心链路（题库、判题、MQ、AI 助理、后台管理）均可用。当前存在两个短板：

1. **缺少用户主页**。后端 `User` 只有 `username/email/role`，无昵称/签名；前端路由无 profile 页面，导航下拉仅有「退出登录」。用户登录后看不到自己的练习成果（提交数、通过题数、通过率、最近提交）。
2. **界面风格不统一**。13 个页面各自写 `<style scoped>`，间距、卡片、色值略有差异；全局仅 `App.vue` 一句底色 `#f5f7fa`，未做 Element Plus 主题定制（`main.js` 直接 `import 'element-plus/dist/index.css'`），视觉偏「默认 Element Plus」。

目标：新增用户主页（资料 + 练习统计 + 最近提交 + 可编辑昵称/签名），并用「全局主题层 + 复用组件 + 定点修饰」的方式统一美化全站，同时给出一份可扩展功能评估。

---

## 一、后端改动（新增用户资料字段与主页接口）

**1. `backend/apps/accounts/models.py`** — 在 `User` 上新增两个可编辑字段：

```python
nickname = models.CharField("昵称", max_length=32, blank=True, default="")
bio = models.CharField("个人简介", max_length=200, blank=True, default="")
```

> 头像**不新增模型字段**：采用前端「首字母 + 确定性渐变色」生成头像（零后端成本）。如需自定义头像上传，需额外配置 `MEDIA_ROOT/MEDIA_URL` 并在服务器挂载卷 + Nginx 反代 `/media/`，列为可选后续项。

**2. 生成迁移**：`python manage.py makemigrations accounts`（新增一个 `000X_*.py`，与现有迁移同目录）。

**3. `backend/apps/accounts/serializers.py`** — 扩展 `UserSerializer`：

- `fields` 增加 `nickname`、`bio`，两者**可写**（用于 `PUT /api/auth/me/` 自我编辑），并在 `fields` 中保持 `role/is_active/date_joined` 只读。
- 新增 `UserProfileSerializer`（资料 + 角色显示名），供主页接口使用。

**4. `backend/apps/accounts/views.py`** — 新增 `UserProfileView`（`RetrieveAPIView`，`permission_classes=[IsAuthenticated]`），路径 `GET /api/users/<id>/profile/`，复用现有 `AdminDashboardView` 的聚合写法（`values().annotate(Count())` + Python 侧 `Counter`）。返回结构：

```jsonc
{
  "user": { "id", "username", "nickname", "bio", "role", "role_display", "date_joined" },
  "stats": {
    "submission_total": 0,        // 总提交数
    "accepted_total": 0,          // 通过提交数（status=accepted）
    "solved_count": 0,            // 通过题目数（problem_id 去重）
    "attempted_count": 0,         // 尝试过的题目数（problem_id 去重）
    "acceptance_rate": 0.0,       // 通过率% = accepted_total / submission_total
    "difficulty_solved": { "easy": 0, "medium": 0, "hard": 0 },
    "language_distribution": [ { "language": "python", "count": 3 } ],
    "status_distribution": [ { "status": "accepted", "count": 5 } ]
  },
  "recent_submissions": [          // 最近 10 条
    { "id", "problem": {"id","title","difficulty"}, "language", "status",
      "time_used_ms", "memory_used_kb", "created_at" }
  ],
  "solved_problem_ids": [1, 2]      // 仅当查看自己时返回，用于题库列表显示「已通过」标记
}
```

统计实现要点（复用 `apps/submissions/models.py` 的 `user` 外键 `related_name="submissions"` 与 `apps/judge/verdicts.py` 的 `Verdict.ACCEPTED`）：

```python
qs = user.submissions.all()
solved_ids = set(qs.filter(status=Verdict.ACCEPTED).values_list("problem_id", flat=True))
# 难度分布：对 solved_ids 取 Problem.difficulty 计数
# 语言/状态分布：qs.values("language"/"status").annotate(count=Count("id"))
```
`Submission` 已有 `(user, -created_at)` 复合索引，最近提交查询无需额外索引。

**5. `backend/apps/accounts/urls.py`** — 新增一条路由（与现有 `auth/me/` 并行的 `users/` 前缀）：

```python
path("users/<int:pk>/profile/", UserProfileView.as_view(), name="user-profile"),
```

---

## 二、前端改动

### 2.1 全局主题层（美化的核心手段）

**新建 `frontend/src/styles/theme.css`**，在 `main.js` 于 `element-plus/dist/index.css` **之后**引入。内容三大块：

1. **设计令牌（`:root`）**：品牌主色（建议由默认 `#409eff` 调整为现代靛蓝渐变体系，集中在 `--brand-*` 变量，一处可改回）、中性色阶、圆角 `8/12/16`、三级阴影、边框色、字体族。
2. **Element Plus 变量覆盖**：`--el-color-primary` 及其 `-light-3/5/7/8/9`、`--el-color-primary-dark-2`、`--el-border-radius-base`、`--el-font-family`、`--el-text-color-primary/regular`、`--el-border-color(-light/-lighter)`、`--el-fill-color-light`、`--el-box-shadow` 等，让所有 el-* 组件自动换肤。
3. **组件级微调**：`el-card` 圆角/边框/阴影、`el-card__header` 字重、`el-table` 表头底色与行 hover、`el-button` 字重与主按钮投影、`el-tag`/`el-pagination` 圆角、`el-menu--horizontal` 选中态、`el-dialog` 圆角、自定义滚动条、路由过渡 `fade-slide`，并新增通用工具类 `.page-header` / `.toolbar` / `.card-grid`。

> 采用「主题层 + 定点修饰」而非逐页重写，是为在 13 个页面间取得一致性，同时把改动集中在少数文件、降低回归风险。

### 2.2 新增复用组件（`frontend/src/components/`）

| 组件 | 作用 |
|---|---|
| `PageHeader.vue` | 统一页头：`title` + `subtitle` + 右侧 `actions` 插槽 |
| `StatCard.vue` | 统计卡片：图标 + 数值 + 标签 + 强调色，供主页与仪表盘复用 |
| `UserAvatar.vue` | 首字母渐变头像：由用户名哈希确定渐变色 + 首字母；`size` 可调 |
| `EmptyState.vue` | 统一空状态：图标 + 文案 + 可选操作 |

### 2.3 用户主页页面

**新建 `frontend/src/views/profile/ProfileView.vue`**，两种使用方式：

- `/profile` → 查看自己；`/users/:id` → 查看他人（复用同组件，`props`/路由参数区分）。

页面结构：左侧资料卡（`UserAvatar` + 昵称/用户名 + 角色 tag + 加入时间 + 简介；本人可见「编辑资料」按钮）｜右侧统计区（4 张 `StatCard`：总提交 / 通过题目 / 通过率 / 尝试题目）｜下方「难度分布（简单/中等/困难 已通过）」+「语言分布」+「最近提交」表格（点击跳 `/submissions/:id`）。编辑资料用 `el-dialog` 表单，提交 `PUT /api/auth/me/`。

**改动清单**：

- `frontend/src/router/index.js`：新增 `{ path: 'profile', component: ProfileView }` 与 `{ path: 'users/:id', component: ProfileView }`（非 `public`，默认需登录）。
- `frontend/src/api/auth.js`（扩展）+ **新建 `frontend/src/api/profile.js`**：`fetchProfile(id)` → `GET /users/{id}/profile/`。
- `frontend/src/stores/auth.js`：`user` 增加 `nickname/bio`，登录后 `fetchMe()` 已可带回；主页编辑成功后调用 `auth.fetchMe()` 刷新。
- `frontend/src/layouts/MainLayout.vue`：右上角下拉触发器改为 `UserAvatar` + 昵称；下拉项新增「个人主页」（→ `/profile`）、「我的提交」（→ `/submissions`），保留「退出登录」。

### 2.4 逐页定点美化（保持各页功能不变）

| 文件 | 修饰点 |
|---|---|
| `layouts/MainLayout.vue` | 头部改为毛玻璃/阴影、logo 用品牌渐变、菜单选中态、主区留白与最大宽度 |
| `views/auth/LoginView.vue` `RegisterView.vue` | 品牌渐变背景 hero + 居中卡片 + 表单间距统一 |
| `views/problems/ProblemListView.vue` | 工具栏（搜索/标签/难度）统一为 `.toolbar`；难度 tag 配色；本人已通过题目显示「已通过」标记 |
| `views/problems/ProblemDetailView.vue` | 左右分栏视觉层次、题目描述卡片、提交区按钮主色 |
| `views/submissions/SubmissionListView.vue` `SubmissionDetailView.vue` | 状态徽章统一（复用 `VerdictBadge.vue`）、表格与工具栏一致 |
| `views/admin/DashboardView.vue` | 顶部 4 张 `StatCard` + 趋势区卡片化 |
| `views/admin/ProblemManageView.vue` `UserManageView.vue` `AdminManageView.vue` | `PageHeader` + 卡片包裹表格 + 批量导入对话框样式 |
| `views/errors/NotFoundView.vue` `ForbiddenView.vue` | 大号图标 + 返回按钮，风格统一 |
| `components/AssistantChat.vue` | 悬浮按钮 + 面板圆角/阴影/滚动区，气泡样式 |
| `components/MarkdownView.vue` `VerdictBadge.vue` `CodeEditor.vue` | 配色与主题一致（编辑器保持 one-dark 不动） |

---

## 三、平台可扩展功能评估（观察结论）

现有架构（每功能一个 Django app + DRF 接口 + Vue 页面；JWT 携带 role 做三级权限；判题走 Celery+Redis MQ 状态机；AI 走 SSE）**对新增功能友好**——多数新增 = 「1 个 app + 1 组接口 + 1 个页面」，不动核心。

**低成本（复用现有模型，1～2 天量级）**
- **排行榜**：基于 `Submission` 聚合（通过题数、通过率、总提交），无需新模型。
- **题目收藏夹**：新增 `Favorite(user, problem)` 关联表 + 列表页/详情页按钮。
- **每日一题**：按日期取 `Problem`，前端卡片展示。
- **题目通过率/难度画像**：在题目列表/详情展示全局通过率（聚合 `Submission`）。
- **代码草稿/历史代码**：`Submission` 已存 `code`，可做「历史代码一键回填编辑器」。

**中成本（需新模型 + 少量流程）**
- **题单/学习路径**：`ProblemList` + `ProblemListItem`，配进度条。
- **竞赛模式**：`Contest` + 报名/榜单快照，判题链路复用现有 MQ。
- **成就徽章**：`Badge` + `UserBadge`，触发条件在判题完成回调里判定。
- **题解/讨论区**：`Solution`/`Comment` 模型（可复用 `MarkdownView` 渲染）。
- **站内通知**：新 app，复用 SSE 或轮询；也可先并入 `assistant` 的消息机制。

**高成本（涉及沙箱与资源）**
- **多语言判题**：现仅 Python（`apps/judge` 语言注册表），扩展 C++/Java 需语言镜像 + 编译步骤。
- **Docker 沙箱隔离**：当前为 subprocess 隔离，强隔离需容器化判题（内存 1.7G 的机器需评估）。
- **判题横向扩容**：独立 judge 容器/多 worker（现 `--concurrency 2`）。
- **实时协作/对战**：需 WebSocket（当前仅 SSE 单向）。

> 结论：平台**可以**持续加功能；建议按「排行榜 → 收藏夹 → 每日一题 → 题单」顺序推进，均低成本且复用现有代码，不必触碰判题核心。

---

## 四、验证方式

**本地**
1. 后端：`python manage.py makemigrations accounts && python manage.py migrate`，启动服务；`GET /api/users/1/profile/` 返回统计字段正确（与 `Submission` 实际数据核对）。
2. 前端：`npm run dev`；检查 `/profile`、`/users/1` 渲染；编辑昵称/签名后刷新可见；题库列表出现「已通过」标记；随机抽查登录、题库、提交、后台、AI 助理页面视觉与功能无回归。

**服务器（`http://101.37.70.252`）**
1. 上传改动文件 → `cd /opt/codepractice/deploy && ./deploy.sh migrate`（应用新迁移）。
2. `./deploy.sh up`（或重建 web 镜像）使前端生效。
3. 用已有账号访问 `/profile` 核对统计；外部（我的机器）验证 `GET /api/users/1/profile/` 200 且字段完整。
4. 回归：登录 `admin/admin123456`、题目列表、提交判题 accepted、AI 助理 SSE 均正常。
5. 最后 `git add/commit/push`（Vercel 自动重新部署）；`.env*` 与密钥不入库。

## 五、风险与注意

- 新增迁移必须在服务器执行 `migrate`，否则新字段查询会 500。
- 主题色若由 `#409eff` 改为靛蓝体系，需确认用户接受品牌色变化；改动集中在 `theme.css` 的令牌，可一键回退。
- 头像不做上传，规避 `MEDIA_ROOT` + Nginx `/media/` 的部署改动。
- 全站美化为纯样式改动，不触碰判题/MQ/AI 逻辑，风险可控。
