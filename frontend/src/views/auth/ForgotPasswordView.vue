<template>
  <div class="auth-page">
    <el-card class="auth-card">
      <h2 class="title">重置密码</h2>
      <p class="subtitle">使用 QQ 邮箱接收验证码，验证通过后即可设置新密码</p>
      <el-form :model="form" label-position="top" @keyup.enter="submit">
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

        <el-form-item label="新密码">
          <el-input v-model="form.password" type="password" show-password placeholder="至少 6 位" />
        </el-form-item>
        <el-form-item label="确认新密码">
          <el-input
            v-model="form.password2"
            type="password"
            show-password
            placeholder="再次输入新密码"
          />
        </el-form-item>

        <el-button type="primary" class="submit-btn" :loading="loading" @click="submit">
          重置密码
        </el-button>
        <div class="footer">
          想起密码了？
          <router-link to="/login">返回登录</router-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { resetPassword, sendEmailCode } from '@/api/auth'

const router = useRouter()

const form = reactive({ email: '', code: '', password: '', password2: '' })
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
    const { data } = await sendEmailCode(email, 'reset')
    ElMessage.success(data.detail || '验证码已发送')
    startCountdown(60)
  } catch (e) {
    ElMessage.error(e.message || '发送失败')
  } finally {
    sending.value = false
  }
}

async function submit() {
  if (!form.email || !form.code || !form.password) {
    ElMessage.warning('请填写完整信息')
    return
  }
  if (!isQqEmail(form.email)) {
    ElMessage.warning('目前仅支持 QQ 邮箱')
    return
  }
  if (!/^\d{6}$/.test(form.code)) {
    ElMessage.warning('验证码应为 6 位数字')
    return
  }
  if (form.password !== form.password2) {
    ElMessage.warning('两次密码不一致')
    return
  }
  loading.value = true
  try {
    await resetPassword({
      email: form.email.trim(),
      code: form.code,
      new_password: form.password,
    })
    ElMessage.success('密码已重置，请使用新密码登录')
    router.push('/login')
  } catch (e) {
    ElMessage.error(e.message || '重置失败')
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
  padding: 32px 16px;
  background: radial-gradient(1200px 600px at 50% -10%, #e8f2fd 0%, transparent 60%), #f5f5f7;
}
.auth-card {
  width: min(420px, calc(100vw - 32px));
  padding: 12px 16px;
  border: none;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-3);
}
.title {
  text-align: center;
  margin: 8px 0 4px;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--c-text);
}
.subtitle {
  text-align: center;
  color: var(--c-text-secondary);
  font-size: 13px;
  margin-bottom: 16px;
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
