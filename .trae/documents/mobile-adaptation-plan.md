# 移动端适配方案

## Context

平台目前是纯桌面布局。整个前端**没有任何媒体查询**（仅 `ProfileView.vue:328` 有一处 `max-width:900px` 用于折叠个人主页栅格），因此在手机上会出现：

- **页面级横向溢出**：顶部导航是横向 `el-menu` 且 `:ellipsis="false"`（`MainLayout.vue:10-27`），最多 6 个菜单项无法收缩，375px 下会撑破页头；
- **固定宽度组件溢出视口**：AI 助理面板固定 `400×560`（`AssistantChat.vue:186-196`）、登录卡 380px、注册/忘记密码卡 420px；
- **对话框溢出**：题目管理页存在 `width="780px"` / `520px` 等内联宽度的对话框；
- **数据表过于拥挤**：各列表页固定列宽合计 720–952px（如提交列表 8 列 = 952px），在 375px 下无法阅读；
- **工具栏**：搜索/筛选控件写死了 `260px / 150px / 140px` 等内联宽度。

目标：在不回归桌面端、不破坏当前苹果风视觉语言的前提下，让手机（375/320px）可正常浏览题库、读题、看提交、登录注册，管理端至少不撑破页面。**性能约束**：不引入新依赖、不使用 `backdrop-filter`、过渡仍 ≤200ms。

## 断点策略

两级断点，与 Element Plus 栅格对齐：

- `max-width: 768px` — 与 EP 的 `xs`（`<768px`）精确一致，保证 `el-row :xs` 已堆叠时 CSS 同步切换；
- `max-width: 560px` — 处理 768 下仍会挤爆的窄屏细节（工具栏满宽、分页收窄、AI 面板）。

## 改动清单

### 1. 新增 `frontend/src/composables/useResponsive.js`

`matchMedia` 封装，返回响应式布尔值；必须在 `onScopeDispose` 中移除监听，避免路由切换泄漏。

```js
export function useMediaQuery(query) { /* mql + ref + listener + onScopeDispose */ }
export const useIsMobile = () => useMediaQuery('(max-width: 768px)')
```

被 4 处复用（题库、我的提交、个人主页、提交详情），值得抽象。

### 2. `frontend/src/styles/theme.css`（全局响应式层，追加在文件末尾）

> 注意：`.main / .header-inner / .main-inner` 在 `MainLayout.vue` 中是 **scoped**，特异性高于 theme.css，必须在该文件内改，不能放这里。此处只处理 EP 内部结构（无 `data-v`）。

```css
@media (max-width: 768px) {
  .el-card__body { padding: 16px; }
  .el-card__header { padding: 14px 16px; }
  .page-header { flex-wrap: wrap; }
  .page-header .page-title { font-size: 22px; }
  .page-header .page-actions { width: 100%; }
  .el-dialog { max-width: calc(100vw - 24px); }   /* 一处修复全部 6 个对话框 */
  .el-table .el-table__cell { padding: 8px 0; }
}
@media (max-width: 560px) {
  .card-grid { grid-template-columns: 1fr; }
  .toolbar .el-input,
  .toolbar .el-select,
  .toolbar .el-input-number { width: 100% !important; flex: 1 1 100%; }
  .toolbar .toolbar-spacer { display: none; }
  .el-pagination .el-pagination__total { display: none; }
}
```

两点取舍说明：

- **对话框用 `max-width` 而非覆盖 `width`**：EP 把 `width="780px"` 写成内联 `--el-dialog-width`，覆盖 `width` 需要 `!important`；`max-width` 未被内联，普通规则即生效，一处生效全部对话框。
- **工具栏内联宽度必须 `!important`**：这些宽度写在模板 `style` 上（题库 260/130/150、提交 160/140、用户管理 220），样式表只有 `!important` 能压过。用 `.toolbar` 前缀把作用域锁死，避免波及页面内其他 `el-input`。重构为 class 改动面更大且易漏，故不采用。

### 3. `frontend/src/layouts/MainLayout.vue`（移动导航）

- 模板：在 `.logo` 前加汉堡按钮 `.nav-toggle`（`display:none`，768 下 `display:inline-flex`）；给现有 `<el-menu>` 加 `.desk-menu` 类并在 768 下 `display:none`；新增 `<el-drawer v-model="drawerOpen" direction="ltr" size="240px" :with-header="false">`，内含 `mode="vertical" router` 的 `el-menu`，**复用同一组菜单项**（题库 / 我的提交 + `isAdmin` / `isSuperAdmin` 条件项），末尾补「个人主页 / 退出登录」。
- 脚本：新增 `drawerOpen` ref；在已有 `watch(() => route.path)` 里追加 `drawerOpen.value = false`；引入 `Menu` 图标。
- 导航纯 CSS 切换，不依赖 composable。
- scoped 媒体查询内同时收紧：`.header-inner { padding: 0 12px }`、`.main { padding: 16px 12px }`、`.logo { margin-right: 12px }`，并隐藏 `.logo-text`、`.user-name`、角色 `el-tag`（保留 `.logo-mark` 与头像下拉）。

### 4. `frontend/src/components/AssistantChat.vue`

纯 CSS 足够，在 scoped 样式末尾追加：

```css
@media (max-width: 560px) {
  .assistant-fab { right: 12px; bottom: calc(12px + env(safe-area-inset-bottom, 0px)); }
  .fab-button { width: 48px; height: 48px; }
  .assistant-panel {
    width: min(400px, calc(100vw - 24px));
    height: min(560px, calc(100vh - 140px));
    height: min(560px, calc(100dvh - 140px));  /* 支持则用动态视口高度 */
    bottom: 60px;
  }
  .panel-header { flex-wrap: wrap; gap: 6px; }
}
```

fab 右缘距视口 12px + 面板 `right:0` → 左右各留 12px，正好贴合。

### 5. 认证页（3 个文件，无需媒体查询）

改宽度公式，桌面端 `min()` 仍取原值，零回归：

- `LoginView.vue:69` → `width: min(380px, calc(100vw - 32px))`；`.auth-page` 的 `height:100vh` 改 `min-height:100vh` 并加 `padding: 16px`。
- `RegisterView.vue:156`、`ForgotPasswordView.vue:143` → `width: min(420px, calc(100vw - 32px))`；`.auth-page` 水平内边距补 `16px`。

320px 下取 288px，无横向滚动。

### 6. 表格策略（核心决策）

**采用混合方案**：

- **面向用户的三处改为卡片列表**（`ProblemListView.vue`、`SubmissionListView.vue`、`ProfileView.vue` 最近提交）：手机主场景是刷题 / 看题 / 查提交，卡片远比 8 列横滚表可用。做法是 `const isMobile = useIsMobile()`，模板 `v-if="!isMobile"` 渲染原 `el-table`、`v-else` 渲染 `.card-list`（**用 v-if 而非 CSS `display:none`**，避免同屏渲染两套 DOM 与重复绑定）。卡片内容：题库 = 标题 + 已通过标记 + 难度 + 标签 + 时限；提交 = 题目 + `VerdictBadge` + 用例 + 耗时 + 时间（整卡可点击跳详情）；个人主页同理复用提交卡片。
- **管理端四个表格保持不变**（题目管理 / 用户管理 / 管理员管理 / 用例抽屉）：手机做数据管理是次要场景，且这些表含 `el-switch`、多按钮操作列、批量导入失败表，卡片化成本与回归风险最高。仅靠第 2 条的单元格内边距压缩 + 容器内原生横向滚动保证可用。

`.stat-grid`（`ProfileView.vue:298`）与 `.card-grid` 已是 `auto-fit/minmax`，手机上自然单列，无需改。

### 7. 编辑器与详情页

- `CodeEditor.vue:70-83`：追加 scoped 媒体查询，手机下 `min-height: 240px; max-height: 46vh; font-size: 13px`。CodeMirror 的 `.cm-scroller` 已可横向滚动，不做换行改造。
- `ProblemDetailView.vue`：**无需改**——已核实 `el-col` 为 `:xs="24" :lg="13"`（L5）与 `:xs="24" :lg="11"`（L56），<768px 自动堆叠。
- `SubmissionDetailView.vue`：`el-descriptions :column="4"`（L18）手机必挤，改为 `:column="isMobile ? 2 : 4"`；`.header`（L4）加 `flex-wrap: wrap`。

## 验证

1. `cd frontend && npm run build` 确认无 CSS/模板语法错误。
2. `npm run dev`，DevTools 设备模拟三档：**375×667、320×568、768×1024**（另加横屏 667×375）。
3. 逐路由检查：`/login`、`/register`、`/forgot-password`、`/problems`、`/problems/:id`、`/submissions`、`/submissions/:id`、`/profile`、`/admin/problems`、`/admin/users`、`/admin/admins`、`/admin/dashboard`、`/403`、随机 404。
4. 每页判定：`document.documentElement.scrollWidth <= window.innerWidth`（无页面级横向滚动）；汉堡可达、抽屉可开且点导航后自动关闭；工具栏控件满宽不溢出；分页不破裂；AI 面板贴合视口；打开「批量导入」「新建题目」「用例」「重置密码 prompt」「编辑资料」确认对话框宽度 = `min(原宽, 100vw-24)`；表格在卡片内横滚而非撑破页面；表单可聚焦；Console 无报错。
5. 回归确认 768–900px 区间（`ProfileView.vue:328` 的 900px 断点早于 768 触发，不冲突）与桌面 1280px 布局无变化。

## 风险 / 回归注意

- **scoped 优先级是最大坑**：`.main/.header-inner` 必须写在 `MainLayout.vue` 的 scoped 样式里，写进 theme.css 会因特异性不足而失效。
- 工具栏内联宽度用 `!important` 是必要妥协，务必保留 `.toolbar` 前缀限定。
- 双分支表格务必用 `v-if`，避免两套 DOM 与事件重复绑定。
- composable 必须注销 `matchMedia` 监听。
- 新增规则无 `blur`、无新依赖，过渡沿用 `--motion-fast/--motion-base`。
- 本次改动**不产生新的未跟踪残留**；本方案文件位于 `.trae/documents/`（该目录下已有两个被 git 跟踪的历史文档），实施后可选择提交或删除。
- 部署（如需）沿用既有流程：本地构建 → 打包 dist → `docker cp` 进 `oj-web` → `docker commit` → compose `--force-recreate --no-build`，**不在服务器构建镜像**。
