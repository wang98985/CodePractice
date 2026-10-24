<template>
  <div>
    <PageHeader title="我的收藏" subtitle="收藏的题目会保存在这里，方便随时回看练习" />

    <el-card shadow="never">
      <el-table v-if="!isMobile" v-loading="loading" :data="rows" stripe>
        <el-table-column label="题目" min-width="260">
          <template #default="{ row }">
            <el-link type="primary" underline="never" @click="$router.push(`/problems/${row.problem.id}`)">
              {{ row.problem.id }}. {{ row.problem.title }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column label="难度" width="100">
          <template #default="{ row }">
            <el-tag
              size="small"
              effect="plain"
              :style="{
                color: difficultyColor(row.problem.difficulty),
                borderColor: difficultyColor(row.problem.difficulty),
              }"
            >
              {{ difficultyText(row.problem.difficulty) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="标签" min-width="180">
          <template #default="{ row }">
            <el-tag
              v-for="t in row.problem.tags"
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
        <el-table-column label="收藏时间" width="180">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-button link type="danger" @click="remove(row)">取消收藏</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 手机端：卡片列表替代表格 -->
      <div v-else v-loading="loading" class="list-cards">
        <div v-for="row in rows" :key="row.id" class="list-card">
          <div class="list-card__head">
            <router-link :to="`/problems/${row.problem.id}`" class="list-card__title">
              {{ row.problem.title }}
            </router-link>
            <el-button link type="danger" size="small" @click="remove(row)">取消收藏</el-button>
          </div>
          <div class="list-card__meta">
            <el-tag
              size="small"
              effect="plain"
              :style="{
                color: difficultyColor(row.problem.difficulty),
                borderColor: difficultyColor(row.problem.difficulty),
              }"
            >
              {{ difficultyText(row.problem.difficulty) }}
            </el-tag>
            <el-tag v-for="t in row.problem.tags" :key="t.id" size="small" type="info" effect="plain">
              {{ t.name }}
            </el-tag>
            <span class="list-card__aux">{{ formatTime(row.created_at) }}</span>
          </div>
        </div>
        <p v-if="!loading && !rows.length" class="text-muted">还没有收藏题目，去题库挑一道吧</p>
      </div>

      <el-empty v-if="!isMobile && !loading && !rows.length" description="还没有收藏题目，去题库挑一道吧">
        <el-button type="primary" @click="$router.push('/problems')">去题库</el-button>
      </el-empty>

      <el-pagination
        v-if="total > pageSize"
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
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listFavorites, removeFavorite } from '@/api/favorites'
import { difficultyColor, difficultyText } from '@/utils/verdict'
import { useIsMobile } from '@/composables/useResponsive'
import PageHeader from '@/components/PageHeader.vue'

const isMobile = useIsMobile()
const rows = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)

function formatTime(t) {
  return t ? new Date(t).toLocaleString('zh-CN', { hour12: false }) : '-'
}

async function load(p = 1) {
  page.value = p
  loading.value = true
  try {
    const { data } = await listFavorites({ page: p })
    rows.value = data.results
    total.value = data.count
    // 取消最后一页的最后一条后自动回退一页，避免出现空页
    if (!data.results.length && p > 1) {
      await load(p - 1)
    }
  } catch (e) {
    ElMessage.error(e.message || '加载失败')
  } finally {
    loading.value = false
  }
}

async function remove(row) {
  try {
    await ElMessageBox.confirm(`确定取消收藏「${row.problem.title}」吗？`, '取消收藏', {
      confirmButtonText: '取消收藏',
      cancelButtonText: '再想想',
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await removeFavorite(row.id)
    ElMessage.success('已取消收藏')
    load(page.value)
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  }
}

onMounted(() => load(1))
</script>
