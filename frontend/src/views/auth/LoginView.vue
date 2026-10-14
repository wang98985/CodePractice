<template>
  <div class="auth-page">
    <el-card class="auth-card">
      <h2 class="title">CodePractice</h2>
      <p class="subtitle">在线代码练习评测平台</p>
      <el-form :model="form" label-position="top" @keyup.enter="submit">
        <el-form-item label="邮箱 / 用户名">
          <el-input v-model="form.email" placeholder="邮箱登录；管理员可填用户名" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" show-password placeholder="密码" />
        </el-form-item>
        <el-button type="primary" class="submit-btn" :loading="loading" @click="submit">
          登录
        </el-button>
        <div class="links">
          <router-link to="/forgot-password">忘记密码？</router-link>
        </div>
        <div class="footer">
          还没有账号？
          <router-link to="/register">立即注册</router-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const form = reactive({ email: '', password: '' })
const loading = ref(false)

async function submit() {
  if (!form.email || !form.password) {
    ElMessage.warning('请输入邮箱/用户名和密码')
    return
  }
  loading.value = true
  try {
    await auth.login(form.email.trim(), form.password)
    ElMessage.success('登录成功')
    router.push(route.query.redirect || '/problems')
  } catch (e) {
    ElMessage.error(e.message || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  padding: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  /* 单层极淡径向光晕 + 纯灰底，成本低、无重绘 */
  background: radial-gradient(1200px 600px at 50% -10%, #e8f2fd 0%, transparent 60%), #f5f5f7;
}
.auth-card {
  width: min(380px, calc(100vw - 32px));
  padding: 12px 16px;
  border: none;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-3);
}
.title {
  text-align: center;
  margin: 8px 0 4px;
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--c-text);
}
.subtitle {
  text-align: center;
  color: var(--c-text-secondary);
  font-size: 13px;
  margin-bottom: 20px;
}
.submit-btn {
  width: 100%;
}
.links {
  text-align: right;
  margin-top: 8px;
  font-size: 13px;
}
.footer {
  text-align: center;
  margin-top: 12px;
  font-size: 13px;
  color: var(--c-text-secondary);
}
</style>
