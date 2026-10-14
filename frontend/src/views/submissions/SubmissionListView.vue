<template>
  <div>
    <PageHeader title="我的提交" subtitle="查看历史提交记录与判题结果" />

    <div class="toolbar">
      <el-select v-model="status" placeholder="状态" clearable style="width: 160px" @change="load(1)">
        <el-option v-for="(v, k) in statusOptions" :key="k" :label="v.text" :value="k" />
      </el-select>
      <el-input-number
        v-model="problemId"
        :min="1"
        placeholder="题目 ID"
        controls-position="hidden"
        style="width: 140px"
        @change="load(1)"
      />
      <el-button @click="load(page)">刷新</el-button>
      <div class="toolbar-spacer" />
      <span class="hint">存在进行中的提交时每 3 秒自动刷新</span>
    </div>

    <el-card shadow="never">
      <el-table v-if="!isMobile" v-loading="loading" :data="rows" stripe>
        <el-table-column prop="id" label="#" width="72" />
        <el-table-column prop="problem_title" label="题目" min-width="200">
          <template #default="{ row }">
            <el-link type="primary" underline="never" @click="$router.push(`/problems/${row.problem}`)">
              {{ row.problem_title }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="130">
          <template #default="{ row }">
            <VerdictBadge :status="row.status" />
          </template>
        </el-table-column>
        <el-table-column label="用例" width="90">
          <template #default="{ row }">{{ row.passed_cases }}/{{ row.total_cases }}</template>
        </el-table-column>
        <el-table-column label="耗时" width="90">
          <template #default="{ row }">{{ row.time_used_ms != null ? row.time_used_ms + 'ms' : '-' }}</template>
        </el-table-column>
        <el-table-column label="内存" width="100">
          <template #default="{ row }">{{ row.memory_used_kb != null ? row.memory_used_kb + 'KB' : '-' }}</template>
        </el-table-column>
        <el-table-column label="语言" prop="language" width="90" />
        <el-table-column prop="created_at" label="提交时间" width="180">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-link type="primary" underline="never" @click="$router.push(`/submissions/${row.id}`)">详情</el-link>
          </template>
        </el-table-column>
      </el-table>

      <!-- 手机端：卡片列表替代表格 -->
      <div v-else v-loading="loading" class="list-cards">
        <router-link
          v-for="row in rows"
          :key="row.id"
          :to="`/submissions/${row.id}`"
          class="list-card is-link"
        >
          <div class="list-card__head">
            <span class="list-card__title">{{ row.problem_title }}</span>
            <VerdictBadge :status="row.status" />
          </div>
          <div class="list-card__meta">
            <span class="list-card__aux">用例 {{ row.passed_cases }}/{{ row.total_cases }}</span>
            <span v-if="row.time_used_ms != null" class="list-card__aux">{{ row.time_used_ms }}ms</span>
            <span class="list-card__aux">{{ row.language }}</span>
            <span class="list-card__aux">{{ formatTime(row.created_at) }}</span>
          </div>
        </router-link>
        <p v-if="!loading && !rows.length" class="text-muted">暂无提交记录</p>
      </div>

      <el-pagination
        layout="prev, pager, next, total"
        :total="total"
        :page-size="pageSize"
        :current-page="page"
        @current-change="load"
      />
    </el-card>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { listSubmissions } from '@/api/submissions'
import { NON_TERMINAL, VERDICT_MAP } from '@/utils/verdict'
import VerdictBadge from '@/components/VerdictBadge.vue'
import { useIsMobile } from '@/composables/useResponsive'
import PageHeader from '@/components/PageHeader.vue'

const statusOptions = computed(() =>
  Object.fromEntries(Object.entries(VERDICT_MAP).filter(([k]) => !NON_TERMINAL.has(k)))
)

const isMobile = useIsMobile()
const rows = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const status = ref('')
const problemId = ref(undefined)
let timer = null

function formatTime(t) {
  return t ? new Date(t).toLocaleString('zh-CN', { hour12: false }) : '-'
}

async function load(p = page.value, silent = false) {
  page.value = p
  if (!silent) loading.value = true
  try {
    const params = { page: p }
    if (status.value) params.status = status.value
    if (problemId.value) params.problem = problemId.value
    const { data } = await listSubmissions(params)
    rows.value = data.results
    total.value = data.count
    scheduleAutoRefresh()
  } catch (e) {
    ElMessage.error(e.message || '加载失败')
  } finally {
    loading.value = false
  }
}

function scheduleAutoRefresh() {
  clearTimeout(timer)
  if (rows.value.some((r) => NON_TERMINAL.has(r.status))) {
    timer = setTimeout(() => load(page.value, true), 3000)
  }
}

onMounted(() => load(1))
onBeforeUnmount(() => clearTimeout(timer))
</script>

<style scoped>
.hint {
  color: var(--c-text-secondary);
  font-size: 12px;
}
</style>
