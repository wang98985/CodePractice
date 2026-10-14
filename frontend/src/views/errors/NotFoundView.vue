<template>
  <div class="error-page">
    <el-icon class="error-icon" :size="86"><Compass /></el-icon>
    <h1 class="error-code">404</h1>
    <p class="error-msg">页面不存在或已被移除</p>
    <el-button type="primary" size="large" @click="$router.push('/problems')">返回题库</el-button>
  </div>
</template>

<script setup>
import { Compass } from '@element-plus/icons-vue'
</script>

<style scoped>
.error-page {
  min-height: 60vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}
.error-icon {
  color: var(--brand-300);
}
.error-code {
  margin: 16px 0 4px;
  font-size: 44px;
  font-weight: 800;
  background: var(--brand-gradient);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.error-msg {
  margin: 0 0 24px;
  color: var(--c-text-secondary);
  font-size: 14px;
}
</style>
