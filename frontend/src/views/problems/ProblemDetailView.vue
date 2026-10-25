<template>
  <div v-loading="loading" class="problem-detail">
    <el-row :gutter="16">
      <!-- 左侧：题面 -->
      <el-col :xs="24" :lg="13">
        <el-card class="desc-card">
          <div class="problem-header">
            <div class="title-row">
              <h2 class="title">{{ problem.id }}. {{ problem.title }}</h2>
              <el-button
                size="small"
                :type="favorited ? 'primary' : ''"
                :plain="favorited"
                :loading="favLoading"
                @click="toggleFav"
              >
                <el-icon style="margin-right: 4px">
                  <StarFilled v-if="favorited" />
                  <Star v-else />
                </el-icon>
                {{ favorited ? '已收藏' : '收藏' }}
              </el-button>
            </div>
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

        <!-- 讨论 / 题解 -->
        <el-card shadow="never" class="discussion-card">
          <div class="discussion-head">
            <span class="discussion-title">讨论与题解</span>
            <el-button size="small" type="primary" plain @click="openPost">发起讨论</el-button>
          </div>

          <el-tabs v-model="kind" @tab-change="loadDiscussions(1)">
            <el-tab-pane label="全部" name="all" />
            <el-tab-pane label="题解" name="solution" />
            <el-tab-pane label="讨论" name="discussion" />
          </el-tabs>

          <div v-loading="discLoading" class="discussion-list">
            <div
              v-for="d in discussions"
              :key="d.id"
              class="discussion-item"
              @click="$router.push(`/discussions/${d.id}`)"
            >
              <div class="discussion-item__head">
                <el-tag v-if="d.is_solution" type="success" effect="plain" size="small">题解</el-tag>
                <span class="discussion-item__title">{{ d.title }}</span>
              </div>
              <div class="discussion-item__meta">
                <span>{{ d.author_nickname }}</span>
                <span>· {{ formatTime(d.created_at) }}</span>
                <span>· {{ d.reply_count }} 回复</span>
              </div>
            </div>
            <p v-if="!discLoading && !discussions.length" class="text-muted discussion-empty">
              还没有讨论，来发第一篇题解吧
            </p>
          </div>

          <el-pagination
            v-if="discTotal > discPageSize"
            small
            layout="prev, pager, next"
            :total="discTotal"
            :page-size="discPageSize"
            :current-page="discPage"
            @current-change="loadDiscussions"
          />
        </el-card>

        <el-dialog v-model="postVisible" title="发起讨论" width="560px" append-to-body>
          <el-form label-position="top">
            <el-form-item label="标题">
              <el-input v-model="postForm.title" maxlength="150" show-word-limit placeholder="一句话说明主题" />
            </el-form-item>
            <el-form-item label="类型">
              <el-radio-group v-model="postForm.is_solution">
                <el-radio :value="false">讨论</el-radio>
                <el-radio :value="true">题解</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="内容（支持 Markdown）">
              <el-input
                v-model="postForm.content"
                type="textarea"
                :rows="8"
                maxlength="20000"
                show-word-limit
                placeholder="分享思路、复杂度分析或踩坑经验"
              />
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="postVisible = false">取消</el-button>
            <el-button type="primary" :loading="posting" @click="submitPost">发表</el-button>
          </template>
        </el-dialog>
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
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Star, StarFilled } from '@element-plus/icons-vue'
import { getProblem } from '@/api/problems'
import { toggleFavorite } from '@/api/favorites'
import { createDiscussion, listDiscussions } from '@/api/discussions'
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
const router = useRouter()
const auth = useAuthStore()
const assistantStore = useAssistantStore()

const problem = ref({})
const loading = ref(true)
const code = ref('')
const language = ref('python')
const submitting = ref(false)
const verdict = ref(null)
const lastSubmissionId = ref(null)
const favorited = ref(false)
const favLoading = ref(false)
let pollTimer = null

// 讨论 / 题解
const kind = ref('all')
const discussions = ref([])
const discTotal = ref(0)
const discPage = ref(1)
const discPageSize = ref(10)
const discLoading = ref(false)
const postVisible = ref(false)
const posting = ref(false)
const postForm = ref({ title: '', content: '', is_solution: false })

const langText = computed(() => language.value)

function formatTime(t) {
  return t ? new Date(t).toLocaleString('zh-CN', { hour12: false }) : '-'
}

async function loadDiscussions(page = 1) {
  if (!problem.value.id) return
  discPage.value = page
  discLoading.value = true
  try {
    const params = { page, page_size: discPageSize.value }
    if (kind.value !== 'all') params.kind = kind.value
    const { data } = await listDiscussions(problem.value.id, params)
    discussions.value = data.results
    discTotal.value = data.count
  } catch (e) {
    ElMessage.error(e.message || '讨论加载失败')
  } finally {
    discLoading.value = false
  }
}

function openPost() {
  if (!auth.isLoggedIn) {
    ElMessage.warning('请先登录')
    return
  }
  postForm.value = { title: '', content: '', is_solution: false }
  postVisible.value = true
}

async function submitPost() {
  if (!postForm.value.title.trim() || !postForm.value.content.trim()) {
    ElMessage.warning('标题和内容都不能为空')
    return
  }
  posting.value = true
  try {
    const { data } = await createDiscussion(problem.value.id, {
      title: postForm.value.title.trim(),
      content: postForm.value.content,
      is_solution: postForm.value.is_solution,
    })
    postVisible.value = false
    ElMessage.success('发表成功')
    router.push(`/discussions/${data.id}`)
  } catch (e) {
    ElMessage.error(e.message || '发表失败')
  } finally {
    posting.value = false
  }
}

onMounted(async () => {
  try {
    const { data } = await getProblem(route.params.id)
    problem.value = data
    favorited.value = Boolean(data.is_favorited)
    language.value = data.allowed_languages?.[0] || 'python'
    code.value = DEFAULT_TEMPLATE[language.value] || ''
    assistantStore.setProblem(data)
    loadDiscussions(1)
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

async function toggleFav() {
  if (!auth.isLoggedIn) {
    ElMessage.warning('请先登录')
    return
  }
  favLoading.value = true
  try {
    const { data } = await toggleFavorite(problem.value.id)
    favorited.value = data.favorited
    ElMessage.success(data.favorited ? '已加入收藏' : '已取消收藏')
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  } finally {
    favLoading.value = false
  }
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
.title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}
.title-row .title {
  margin: 0 0 8px;
  min-width: 0;
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
.discussion-card {
  margin-bottom: 16px;
}
.discussion-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}
.discussion-title {
  font-weight: 600;
  font-size: 15px;
}
.discussion-item {
  padding: 10px 0;
  border-top: 1px solid var(--c-border-light);
  cursor: pointer;
}
.discussion-item:hover .discussion-item__title {
  color: var(--brand-500);
}
.discussion-item__head {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.discussion-item__title {
  font-size: 14px;
  color: var(--c-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.discussion-item__meta {
  display: flex;
  gap: 6px;
  margin-top: 4px;
  font-size: 12px;
  color: var(--c-text-secondary);
}
.discussion-empty {
  font-size: 13px;
  padding: 12px 0 4px;
}
</style>
