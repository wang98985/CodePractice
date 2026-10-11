<template>
  <el-card>
    <div class="toolbar">
      <el-input
        v-model="filters.search"
        placeholder="搜索题目"
        clearable
        style="width: 240px"
        @keyup.enter="load(1)"
        @clear="load(1)"
      >
        <template #append>
          <el-button @click="load(1)"><el-icon><Search /></el-icon></el-button>
        </template>
      </el-input>
      <el-select v-model="filters.difficulty" placeholder="难度" clearable style="width: 120px" @change="load(1)">
        <el-option label="简单" value="easy" />
        <el-option label="中等" value="medium" />
        <el-option label="困难" value="hard" />
      </el-select>
      <el-select v-model="filters.tag" placeholder="标签" clearable style="width: 140px" @change="load(1)">
        <el-option v-for="t in tags" :key="t.id" :label="t.name" :value="t.name" />
      </el-select>
    </div>

    <el-table v-loading="loading" :data="problems" stripe>
      <el-table-column prop="id" label="#" width="64" />
      <el-table-column label="标题" min-width="240">
        <template #default="{ row }">
          <el-link type="primary" @click="$router.push(`/problems/${row.id}`)">
            {{ row.title }}
          </el-link>
        </template>
      </el-table-column>
      <el-table-column label="难度" width="100">
        <template #default="{ row }">
          <span :style="{ color: difficultyColor(row.difficulty), fontWeight: 600 }">
            {{ difficultyText(row.difficulty) }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="标签" min-width="160">
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
      class="pagination"
      layout="prev, pager, next, total"
      :total="total"
      :page-size="pageSize"
      :current-page="page"
      @current-change="load"
    />
  </el-card>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { listProblems, listTags } from '@/api/problems'
import { difficultyColor, difficultyText } from '@/utils/verdict'

const problems = ref([])
const tags = ref([])
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
})
</script>

<style scoped>
.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
.pagination {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>
