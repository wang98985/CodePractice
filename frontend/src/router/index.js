import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  { path: '/login', component: () => import('@/views/auth/LoginView.vue'), meta: { public: true } },
  { path: '/register', component: () => import('@/views/auth/RegisterView.vue'), meta: { public: true } },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    children: [
      { path: '', redirect: '/problems' },
      { path: 'problems', component: () => import('@/views/problems/ProblemListView.vue') },
      { path: 'problems/:id', component: () => import('@/views/problems/ProblemDetailView.vue') },
      { path: 'profile', component: () => import('@/views/profile/ProfileView.vue') },
      { path: 'users/:id', component: () => import('@/views/profile/ProfileView.vue') },
      { path: 'submissions', component: () => import('@/views/submissions/SubmissionListView.vue') },
      { path: 'submissions/:id', component: () => import('@/views/submissions/SubmissionDetailView.vue') },
      { path: 'admin', redirect: '/admin/problems' },
      {
        path: 'admin/problems',
        component: () => import('@/views/admin/ProblemManageView.vue'),
        meta: { roles: ['admin', 'super_admin'] },
      },
      {
        path: 'admin/users',
        component: () => import('@/views/admin/UserManageView.vue'),
        meta: { roles: ['admin', 'super_admin'] },
      },
      {
        path: 'admin/admins',
        component: () => import('@/views/admin/AdminManageView.vue'),
        meta: { roles: ['super_admin'] },
      },
      {
        path: 'admin/dashboard',
        component: () => import('@/views/admin/DashboardView.vue'),
        meta: { roles: ['super_admin'] },
      },
    ],
  },
  { path: '/403', component: () => import('@/views/errors/ForbiddenView.vue') },
  { path: '/:pathMatch(.*)*', component: () => import('@/views/errors/NotFoundView.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (!to.meta.public && !auth.isLoggedIn) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  if (to.meta.roles && !to.meta.roles.includes(auth.role)) {
    return { path: '/403' }
  }
})

// 懒加载 chunk 加载失败时（旧缓存壳引用已删除的 chunk、网络抖动）自动整页刷新，避免静默白屏
router.onError((error) => {
  if (/Loading chunk|Failed to fetch dynamically imported module|ChunkLoadError/i.test(error.message)) {
    window.location.reload()
  }
})

export default router
