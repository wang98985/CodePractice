<template>
  <div>
    <PageHeader title="题库" subtitle="挑一道题开始练习，支持关键词、难度与标签筛选" />

    <div class="toolbar">
      <el-input
        v-model="filters.search"
        placeholder="搜索题目"
        clearable
        style="width: 260px"
        @keyup.enter="load(1)"
        @clear="load(1)"
      >
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-select v-model="filters.difficulty" placeholder="难度" clearable style="width: 130px" @change="load(1)">
        <el-option label="简单" value="easy" />
        <el-option label="中等" value="medium" />
        <el-option label="困难" value="hard" />
      </el-select>
      <el-select v-model="filters.tag" placeholder="标签" clearable style="width: 150px" @change="load(1)">
        <el-option v-for="t in tags" :key="t.id" :label="t.name" :value="t.name" />
      </el-select>
      <div class="toolbar-spacer" />
      <el-button @click="load(1)">刷新</el-button>
    </div>

    <el-card shadow="never">
      <el-table v-loading="loading" :data="problems" stripe>
        <el-table-column prop="id" label="#" width="64" />
        <el-table-column label="标题" min-width="260">
          <template #default="{ row }">
            <el-link type="primary" :underline="false" @click="$router.push(`/problems/${row.id}`)">
              {{ row.title }}
            </el-link>
            <el-tag
              v-if="solvedIds.has(row.id)"
              size="small"
              type="success"
              effect="plain"
              style="margin-left: 8px"
            >
              已通过
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="难度" width="100">
          <template #default="{ row }">
            <el-tag
              size="small"
              effect="plain"
              :style="{ color: difficultyColor(row.difficulty), borderColor: difficultyColor(row.difficulty) }"
            >
              {{ difficultyText(row.difficulty) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="标签" min-width="180">
          <template #default="{ row }">
            <el-tag
              v-for="t in row.tags"
              :key="t.id"
              size="small"
              type="info"
              effect="plain"
              style="margin-right: 4px"
            >
              {{ t.name }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="时限/内存" width="150">
          <template #default="{ row }">
            {{ row.time_limit_ms }}ms / {{ Math.round(row.memory_limit_kb / 1024) }}MB
          </template>
        </el-table-column>
      </el-table>

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
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { listProblems, listTags } from '@/api/problems'
import { fetchProfile } from '@/api/profile'
import { useAuthStore } from '@/stores/auth'
import { difficultyColor, difficultyText } from '@/utils/verdict'
import PageHeader from '@/components/PageHeader.vue'

const auth = useAuthStore()
const problems = ref([])
const tags = ref([])
const solvedIds = ref(new Set())
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const filters = reactive({ search: '', difficulty: '', tag: '' })

async function load(p = page.value) {
  page.value = p
  loading.value = true
  try {
    const params = { page: p }
    if (filters.search) params.search = filters.search
    if (filters.difficulty) params.difficulty = filters.difficulty
    if (filters.tag) params.tag = filters.tag
    const { data } = await listProblems(params)
    problems.value = data.results
    total.value = data.count
  } catch (e) {
    ElMessage.error(e.message || '加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  load(1)
  try {
    const { data } = await listTags()
    tags.value = data
  } catch { /* ignore */ }
  if (auth.user?.id) {
    try {
      const { data } = await fetchProfile(auth.user.id)
      solvedIds.value = new Set(data.solved_problem_ids || [])
    } catch { /* ignore */ }
  }
})
</script>
