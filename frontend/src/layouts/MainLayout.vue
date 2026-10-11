<template>
  <el-container class="main-layout">
    <el-header class="header">
      <div class="logo" @click="$router.push('/problems')">CodePractice</div>

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

      <el-dropdown v-if="auth.isLoggedIn" @command="handleCommand">
        <span class="user-info">
          {{ auth.user?.username }}
          <el-tag size="small" :type="roleTagType" effect="plain">{{ roleText }}</el-tag>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="logout">退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
      <el-button v-else type="primary" text @click="$router.push('/login')">登录</el-button>
    </el-header>

    <el-main class="main">
      <router-view />
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

const auth = useAuthStore()
const assistantStore = useAssistantStore()
const route = useRoute()
const router = useRouter()

const activeMenu = computed(() => '/' + route.path.split('/')[1])
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
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  padding: 0 32px;
}
.logo {
  font-size: 20px;
  font-weight: 700;
  color: #409eff;
  cursor: pointer;
  margin-right: 40px;
  white-space: nowrap;
}
.menu {
  flex: 1;
  border-bottom: none;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  outline: none;
}
.main {
  padding: 20px 32px;
}
</style>
