<template>
  <div v-loading="loading" class="problem-detail">
    <el-row :gutter="16">
      <!-- 左侧：题面 -->
      <el-col :xs="24" :lg="13">
        <el-card class="desc-card">
          <div class="problem-header">
            <h2 class="title">{{ problem.id }}. {{ problem.title }}</h2>
            <div class="meta">
              <el-tag
                size="small"
                effect="plain"
                :style="{ color: difficultyColor(problem.difficulty), borderColor: difficultyColor(problem.difficulty) }"
              >
                {{ difficultyText(problem.difficulty) }}
              </el-tag>
              <el-divider direction="vertical" />
              <span>时限 {{ problem.time_limit_ms }}ms</span>
              <el-divider direction="vertical" />
              <span>内存 {{ Math.round(problem.memory_limit_kb / 1024) }}MB</span>
              <template v-for="t in problem.tags" :key="t.id">
                <el-tag size="small" type="info" effect="plain" style="margin-left: 8px">
                  {{ t.name }}
                </el-tag>
              </template>
            </div>
          </div>

          <MarkdownView :content="problem.description || ''" />

          <template v-if="problem.sample_cases?.length">
            <h3>示例</h3>
            <div v-for="(c, i) in problem.sample_cases" :key="c.id" class="sample-case">
              <div class="io-block">
                <div class="io-label">输入 #{{ i + 1 }}</div>
                <pre class="io-pre">{{ c.input_data }}</pre>
              </div>
              <div class="io-block">
                <div class="io-label">输出 #{{ i + 1 }}</div>
                <pre class="io-pre">{{ c.expected_output }}</pre>
              </div>
            </div>
          </template>

          <div v-if="problem.reference_answer" class="reference">
            <el-collapse>
              <el-collapse-item title="参考答案（管理员可见）">
                <pre class="io-pre">{{ problem.reference_answer }}</pre>
              </el-collapse-item>
            </el-collapse>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：提交面板 -->
      <el-col :xs="24" :lg="11">
        <el-card class="submit-card">
          <div class="submit-header">
            <span class="submit-title">提交代码</span>
            <el-select v-model="language" style="width: 140px">
              <el-option
                v-for="lang in problem.allowed_languages || ['python']"
                :key="lang"
                :label="lang"
                :value="lang"
              />
            </el-select>
          </div>

          <CodeEditor v-model="code" :language="language" />

          <div class="submit-actions">
            <el-button type="primary" :loading="submitting" @click="submit">
              提交评测
            </el-button>
            <el-button @click="resetCode">重置</el-button>
          </div>

          <!-- 判题结果横幅 -->
          <el-alert
            v-if="verdict"
            class="verdict-banner"
            :title="`${verdictText(verdict.status)}  ${verdict.passed_cases}/${verdict.total_cases} 用例通过`"
            :type="verdictType(verdict.status) === 'danger' ? 'error' : verdictType(verdict.status)"
            :closable="false"
            show-icon
          >
            <div v-if="verdict.status !== 'pending' && verdict.status !== 'judging'" class="verdict-stats">
              耗时 {{ verdict.time_used_ms ?? '-' }}ms ·
              内存 {{ verdict.memory_used_kb != null ? Math.round(verdict.memory_used_kb) + 'KB' : '-' }}
              <el-link type="primary" @click="$router.push(`/submissions/${lastSubmissionId}`)">
                查看详情
              </el-link>
            </div>
          </el-alert>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getProblem } from '@/api/problems'
import { createSubmission, getSubmissionStatus } from '@/api/submissions'
import { useAuthStore } from '@/stores/auth'
import { useAssistantStore } from '@/stores/assistant'
import { difficultyColor, difficultyText, NON_TERMINAL, verdictText, verdictType } from '@/utils/verdict'
import CodeEditor from '@/components/CodeEditor.vue'
import MarkdownView from '@/components/MarkdownView.vue'

const DEFAULT_TEMPLATE = {
  python: '',
  cpp: '',
  java: '',
}

const route = useRoute()
const auth = useAuthStore()
const assistantStore = useAssistantStore()

const problem = ref({})
const loading = ref(true)
const code = ref('')
const language = ref('python')
const submitting = ref(false)
const verdict = ref(null)
const lastSubmissionId = ref(null)
let pollTimer = null

const langText = computed(() => language.value)

onMounted(async () => {
  try {
    const { data } = await getProblem(route.params.id)
    problem.value = data
    language.value = data.allowed_languages?.[0] || 'python'
    code.value = DEFAULT_TEMPLATE[language.value] || ''
    assistantStore.setProblem(data)
  } catch (e) {
    ElMessage.error(e.message || '题目加载失败')
  } finally {
    loading.value = false
  }
})

onBeforeUnmount(() => {
  clearTimeout(pollTimer)
  assistantStore.clearProblem()
})

function resetCode() {
  code.value = DEFAULT_TEMPLATE[language.value] || ''
}

async function submit() {
  if (!auth.isLoggedIn) {
    ElMessage.warning('请先登录')
    return
  }
  if (!code.value.trim()) {
    ElMessage.warning('代码不能为空')
    return
  }
  submitting.value = true
  verdict.value = null
  try {
    const { data } = await createSubmission({
      problem: problem.value.id,
      language: langText.value,
      code: code.value,
    })
    lastSubmissionId.value = data.id
    verdict.value = { status: 'pending', passed_cases: 0, total_cases: 0 }
    pollStatus(data.id)
  } catch (e) {
    ElMessage.error(e.message || '提交失败')
  } finally {
    submitting.value = false
  }
}

async function pollStatus(id) {
  try {
    const { data } = await getSubmissionStatus(id)
    verdict.value = data
    if (NON_TERMINAL.has(data.status)) {
      pollTimer = setTimeout(() => pollStatus(id), 1500)
    }
  } catch {
    pollTimer = setTimeout(() => pollStatus(id), 3000)
  }
}
</script>

<style scoped>
.desc-card {
  margin-bottom: 16px;
}
.submit-card {
  margin-bottom: 16px;
}
.problem-header .title {
  margin: 0 0 8px;
  font-size: 20px;
}
.meta {
  display: flex;
  align-items: center;
  color: var(--c-text-regular);
  font-size: 13px;
  margin-bottom: 12px;
}
.sample-case {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}
.io-block {
  flex: 1;
  min-width: 0;
}
.io-label {
  font-size: 12px;
  color: var(--c-text-secondary);
  margin-bottom: 4px;
}
.io-pre {
  background: var(--c-bg);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-sm);
  padding: 8px 12px;
  margin: 0;
  font-size: 13px;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 180px;
  overflow-y: auto;
}
.reference {
  margin-top: 12px;
}
.submit-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.submit-title {
  font-weight: 600;
}
.submit-actions {
  margin: 12px 0;
  display: flex;
  gap: 8px;
}
.verdict-banner {
  margin-top: 8px;
}
.verdict-stats {
  font-size: 12px;
  color: var(--c-text-regular);
  display: flex;
  gap: 8px;
  align-items: center;
}
</style>
