<template>
  <el-container class="main-layout">
    <el-header class="header">
      <div class="header-inner">
        <el-button class="nav-toggle" text aria-label="打开导航" @click="drawerOpen = true">
          <el-icon :size="22"><Menu /></el-icon>
        </el-button>

        <div class="logo" @click="$router.push('/problems')">
          <span class="logo-mark">CP</span>
          <span class="logo-text">CodePractice</span>
        </div>

        <el-menu
          mode="horizontal"
          router
          :default-active="activeMenu"
          class="menu desk-menu"
          :ellipsis="false"
        >
          <el-menu-item index="/problems">题库</el-menu-item>
          <el-menu-item index="/daily">每日一题</el-menu-item>
          <el-menu-item index="/problem-sets">题单</el-menu-item>
          <el-menu-item index="/leaderboard">排行榜</el-menu-item>
          <el-menu-item index="/favorites">收藏夹</el-menu-item>
          <el-menu-item index="/submissions">我的提交</el-menu-item>
          <template v-if="auth.isAdmin">
            <el-menu-item index="/admin/problems">题目管理</el-menu-item>
            <el-menu-item index="/admin/users">用户管理</el-menu-item>
          </template>
          <template v-if="auth.isSuperAdmin">
            <el-menu-item index="/admin/admins">管理员管理</el-menu-item>
            <el-menu-item index="/admin/dashboard">仪表盘</el-menu-item>
          </template>
        </el-menu>

        <el-dropdown v-if="auth.isLoggedIn" trigger="click" @command="handleCommand">
          <span class="user-info">
            <UserAvatar :name="displayName" :size="30" />
            <span class="user-name">{{ displayName }}</span>
            <el-tag class="user-role-tag" size="small" :type="roleTagType" effect="plain">{{ roleText }}</el-tag>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">个人主页</el-dropdown-item>
              <el-dropdown-item command="submissions">我的提交</el-dropdown-item>
              <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button v-else type="primary" @click="$router.push('/login')">登录</el-button>
      </div>
    </el-header>

    <el-main class="main">
      <div class="main-inner">
        <router-view />
      </div>
    </el-main>

    <AssistantChat />
  </el-container>

  <!-- 窄屏导航抽屉：复用同一组菜单项 -->
  <el-drawer
    v-model="drawerOpen"
    direction="ltr"
    size="250px"
    :with-header="false"
    class="nav-drawer"
  >
    <el-menu mode="vertical" router :default-active="activeMenu" class="drawer-menu">
      <el-menu-item index="/problems">题库</el-menu-item>
      <el-menu-item index="/daily">每日一题</el-menu-item>
      <el-menu-item index="/problem-sets">题单</el-menu-item>
      <el-menu-item index="/leaderboard">排行榜</el-menu-item>
      <el-menu-item index="/favorites">收藏夹</el-menu-item>
      <el-menu-item index="/submissions">我的提交</el-menu-item>
      <template v-if="auth.isAdmin">
        <el-menu-item index="/admin/problems">题目管理</el-menu-item>
        <el-menu-item index="/admin/users">用户管理</el-menu-item>
      </template>
      <template v-if="auth.isSuperAdmin">
        <el-menu-item index="/admin/admins">管理员管理</el-menu-item>
        <el-menu-item index="/admin/dashboard">仪表盘</el-menu-item>
      </template>
      <el-menu-item v-if="auth.isLoggedIn" index="/profile">个人主页</el-menu-item>
    </el-menu>
    <div v-if="auth.isLoggedIn" class="drawer-footer">
      <el-button class="drawer-logout" @click="handleCommand('logout')">退出登录</el-button>
    </div>
  </el-drawer>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Menu } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useAssistantStore } from '@/stores/assistant'
import AssistantChat from '@/components/AssistantChat.vue'
import UserAvatar from '@/components/UserAvatar.vue'

const auth = useAuthStore()
const assistantStore = useAssistantStore()
const route = useRoute()
const router = useRouter()

const drawerOpen = ref(false)
const activeMenu = computed(() => '/' + route.path.split('/')[1])
const displayName = computed(() => auth.user?.nickname || auth.user?.email || '')
const roleText = computed(
  () => ({ user: '普通用户', admin: '管理员', super_admin: '超级管理员' }[auth.role] || auth.role)
)
const roleTagType = computed(
  () => ({ user: 'info', admin: 'warning', super_admin: 'danger' }[auth.role] || 'info')
)

// 离开题目详情页时清除 AI 上下文
watch(
  () => route.path,
  (path) => {
    drawerOpen.value = false
    if (!path.startsWith('/problems/')) assistantStore.clearProblem()
  }
)

function handleCommand(cmd) {
  if (cmd === 'logout') {
    auth.logout()
    router.push('/login')
  } else if (cmd === 'profile') {
    router.push('/profile')
  } else if (cmd === 'submissions') {
    router.push('/submissions')
  }
}
</script>

<style scoped>
.main-layout {
  height: 100%;
}
.header {
  display: flex;
  align-items: center;
  height: 56px;
  padding: 0;
  /* 纯色实底：不用 backdrop-filter，避免滚动时大面积重绘 */
  background: #ffffff;
  border-bottom: 1px solid var(--c-border-light);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
  z-index: 100;
}
.header-inner {
  width: 100%;
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  align-items: center;
}
.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  margin-right: 36px;
  white-space: nowrap;
}
.logo-mark {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--brand-500);
  color: #fff;
  font-weight: 600;
  font-size: 13px;
  letter-spacing: 0.02em;
}
.logo-text {
  font-size: 17px;
  font-weight: 600;
  letter-spacing: -0.02em;
  color: var(--c-text);
}
.menu {
  flex: 1;
  border-bottom: none;
  background: transparent;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  outline: none;
  padding-left: 8px;
}
.user-name {
  font-weight: 500;
  color: var(--c-text);
}
.main {
  padding: 32px 24px;
  background: var(--c-bg);
}
.main-inner {
  max-width: 1280px;
  margin: 0 auto;
}

/* ---------------- 窄屏导航 ---------------- */
.nav-toggle {
  display: none;
  margin-right: 4px;
}
.drawer-menu {
  border-right: none;
}
.drawer-footer {
  padding: 12px 16px;
  border-top: 1px solid var(--c-border-light);
}
.drawer-logout {
  width: 100%;
}

@media (max-width: 768px) {
  .nav-toggle {
    display: inline-flex;
  }
  /* 横向菜单无法收缩（:ellipsis="false"），窄屏整体隐藏，改用抽屉 */
  .desk-menu {
    display: none;
  }
  .header-inner {
    padding: 0 12px;
  }
  .logo {
    margin-right: 12px;
  }
  .logo-text {
    display: none;
  }
  .user-name,
  .user-role-tag {
    display: none;
  }
  .main {
    padding: 16px 12px;
  }
}
</style>
