<template>
  <div class="auth-page">
    <el-card class="auth-card">
      <h2 class="title">注册账号</h2>
      <el-form :model="form" label-position="top" @keyup.enter="submit">
        <el-form-item label="用户名">
          <el-input v-model="form.username" placeholder="用户名" />
        </el-form-item>

        <el-form-item label="邮箱（仅支持 QQ 邮箱）">
          <el-input v-model="form.email" placeholder="例如：123456@qq.com" />
        </el-form-item>

        <el-form-item label="验证码">
          <div class="code-row">
            <el-input v-model="form.code" maxlength="6" placeholder="6 位数字验证码" />
            <el-button
              :disabled="countdown > 0 || sending"
              :loading="sending"
              @click="sendCode"
            >
              {{ countdown > 0 ? `${countdown} 秒后重发` : '获取验证码' }}
            </el-button>
          </div>
        </el-form-item>

        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" show-password placeholder="至少 6 位" />
        </el-form-item>
        <el-form-item label="确认密码">
          <el-input v-model="form.password2" type="password" show-password placeholder="再次输入密码" />
        </el-form-item>

        <el-button type="primary" class="submit-btn" :loading="loading" @click="submit">
          注册
        </el-button>
        <div class="footer">
          已有账号？
          <router-link to="/login">直接登录</router-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { sendEmailCode } from '@/api/auth'

const auth = useAuthStore()
const router = useRouter()

const form = reactive({ username: '', email: '', code: '', password: '', password2: '' })
const loading = ref(false)
const sending = ref(false)
const countdown = ref(0)

function isQqEmail(email) {
  return /^[1-9]\d{4,10}@qq\.com$/i.test(email.trim())
}

let timer = null
function startCountdown(seconds) {
  countdown.value = seconds
  timer && clearInterval(timer)
  timer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      clearInterval(timer)
      timer = null
    }
  }, 1000)
}

async function sendCode() {
  const email = form.email.trim()
  if (!email) {
    ElMessage.warning('请先填写邮箱')
    return
  }
  if (!isQqEmail(email)) {
    ElMessage.warning('目前仅支持 QQ 邮箱（格式：123456@qq.com）')
    return
  }
  sending.value = true
  try {
    const { data } = await sendEmailCode(email)
    ElMessage.success(data.detail || '验证码已发送')
    startCountdown(60)
  } catch (e) {
    const msg = e.response?.data?.detail || e.response?.data?.email?.[0] || e.message || '发送失败'
    ElMessage.error(msg)
  } finally {
    sending.value = false
  }
}

async function submit() {
  if (!form.username || !form.email || !form.code || !form.password) {
    ElMessage.warning('请填写完整信息')
    return
  }
  if (!isQqEmail(form.email)) {
    ElMessage.warning('目前仅支持 QQ 邮箱注册')
    return
  }
  if (form.password !== form.password2) {
    ElMessage.warning('两次密码不一致')
    return
  }
  if (!/^\d{6}$/.test(form.code)) {
    ElMessage.warning('验证码应为 6 位数字')
    return
  }
  loading.value = true
  try {
    await auth.register({
      username: form.username,
      email: form.email,
      password: form.password,
      code: form.code,
    })
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } catch (e) {
    const msg = e.response?.data?.detail
      || e.response?.data?.code?.[0]
      || e.response?.data?.email?.[0]
      || e.response?.data?.username?.[0]
      || e.message
      || '注册失败'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px 0;
  background: radial-gradient(circle at 18% 18%, #e0e7ff 0%, transparent 55%),
    radial-gradient(circle at 82% 82%, #dbeafe 0%, transparent 55%),
    linear-gradient(135deg, #f6f7fb 0%, #eef1fb 100%);
}
.auth-card {
  width: 420px;
  padding: 12px 16px;
  border: none;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-3);
}
.title {
  text-align: center;
  margin: 8px 0 16px;
  font-size: 22px;
  font-weight: 800;
  background: var(--brand-gradient);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.code-row {
  display: flex;
  gap: 8px;
}
.code-row .el-input {
  flex: 1;
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
