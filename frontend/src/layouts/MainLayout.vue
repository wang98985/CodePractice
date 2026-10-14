<template>
  <el-container class="main-layout">
    <el-header class="header">
      <div class="header-inner">
        <div class="logo" @click="$router.push('/problems')">
          <span class="logo-mark">CP</span>
          <span class="logo-text">CodePractice</span>
        </div>

        <el-menu
          mode="horizontal"
          router
          :default-active="activeMenu"
          class="menu"
          :ellipsis="false"
        >
          <el-menu-item index="/problems">题库</el-menu-item>
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
            <el-tag size="small" :type="roleTagType" effect="plain">{{ roleText }}</el-tag>
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
        <router-view v-slot="{ Component }">
          <transition name="fade-slide" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </el-main>

    <AssistantChat />
  </el-container>
</template>

<script setup>
import { computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAssistantStore } from '@/stores/assistant'
import AssistantChat from '@/components/AssistantChat.vue'
import UserAvatar from '@/components/UserAvatar.vue'

const auth = useAuthStore()
const assistantStore = useAssistantStore()
const route = useRoute()
const router = useRouter()

const activeMenu = computed(() => '/' + route.path.split('/')[1])
const displayName = computed(() => auth.user?.nickname || auth.user?.username || '')
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
  height: 60px;
  padding: 0;
  background: rgba(255, 255, 255, 0.86);
  backdrop-filter: saturate(180%) blur(12px);
  border-bottom: 1px solid var(--c-border);
  box-shadow: 0 1px 2px rgba(24, 32, 59, 0.04);
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
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--brand-gradient);
  color: #fff;
  font-weight: 700;
  font-size: 13px;
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
}
.logo-text {
  font-size: 18px;
  font-weight: 700;
  background: var(--brand-gradient);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
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
  padding: 24px;
  background: var(--c-bg);
}
.main-inner {
  max-width: 1280px;
  margin: 0 auto;
}
</style>
