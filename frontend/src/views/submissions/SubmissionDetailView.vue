<template>
  <el-card v-loading="loading">
    <template #header>
      <div class="header">
        <div class="header-left">
          <el-button text @click="$router.push('/submissions')">
            <el-icon><ArrowLeft /></el-icon> 返回列表
          </el-button>
          <span class="title">#{{ submission.id }} · {{ submission.problem_title }}</span>
          <VerdictBadge :status="submission.status" />
        </div>
        <el-button text type="primary" @click="$router.push(`/problems/${submission.problem}`)">
          查看题目
        </el-button>
      </div>
    </template>

    <el-descriptions :column="isMobile ? 2 : 4" border size="small" class="stats">
      <el-descriptions-item label="用例通过">
        {{ submission.passed_cases }}/{{ submission.total_cases }}
      </el-descriptions-item>
      <el-descriptions-item label="耗时">
        {{ submission.time_used_ms != null ? submission.time_used_ms + 'ms' : '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="内存">
        {{ submission.memory_used_kb != null ? submission.memory_used_kb + 'KB' : '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="语言">{{ submission.language }}</el-descriptions-item>
    </el-descriptions>

    <el-alert
      v-if="submission.error_message"
      type="error"
      class="error-box"
      title="错误信息"
      :closable="false"
    >
      <pre class="error-pre">{{ submission.error_message }}</pre>
    </el-alert>

    <h3>提交代码</h3>
    <CodeEditor :model-value="submission.code || ''" :language="submission.language || 'python'" />
  </el-card>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getSubmission } from '@/api/submissions'
import { NON_TERMINAL } from '@/utils/verdict'
import CodeEditor from '@/components/CodeEditor.vue'
import VerdictBadge from '@/components/VerdictBadge.vue'
import { useIsMobile } from '@/composables/useResponsive'

const route = useRoute()
const isMobile = useIsMobile()
const submission = ref({})
const loading = ref(true)
let timer = null

async function load(silent = false) {
  if (!silent) loading.value = true
  try {
    const { data } = await getSubmission(route.params.id)
    submission.value = data
    clearTimeout(timer)
    if (NON_TERMINAL.has(data.status)) {
      timer = setTimeout(() => load(true), 2000)
    }
  } catch (e) {
    ElMessage.error(e.message || '加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => load())
onBeforeUnmount(() => clearTimeout(timer))
</script>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
@media (max-width: 560px) {
  .header {
    flex-wrap: wrap;
    gap: 8px;
  }
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.title {
  font-weight: 600;
}
.stats {
  margin-bottom: 16px;
}
.error-box {
  margin-bottom: 16px;
}
.error-pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
  font-size: 12px;
  max-height: 200px;
  overflow-y: auto;
}
</style>
