<template>
  <div class="auth-page">
    <el-card class="auth-card">
      <h2 class="title">CodePractice</h2>
      <p class="subtitle">在线代码练习评测平台</p>
      <el-form :model="form" label-position="top" @keyup.enter="submit">
        <el-form-item label="用户名">
          <el-input v-model="form.username" placeholder="用户名" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" show-password placeholder="密码" />
        </el-form-item>
        <el-button type="primary" class="submit-btn" :loading="loading" @click="submit">
          登录
        </el-button>
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

const form = reactive({ username: '', password: '' })
const loading = ref(false)

async function submit() {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    await auth.login(form.username, form.password)
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
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(circle at 18% 18%, #e0e7ff 0%, transparent 55%),
    radial-gradient(circle at 82% 82%, #dbeafe 0%, transparent 55%),
    linear-gradient(135deg, #f6f7fb 0%, #eef1fb 100%);
}
.auth-card {
  width: 380px;
  padding: 12px 16px;
  border: none;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-3);
}
.title {
  text-align: center;
  margin: 8px 0 4px;
  font-size: 24px;
  font-weight: 800;
  background: var(--brand-gradient);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
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
.footer {
  text-align: center;
  margin-top: 12px;
  font-size: 13px;
  color: var(--c-text-secondary);
}
</style>
