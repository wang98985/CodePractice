<template>
  <div v-loading="loading">
    <PageHeader title="仪表盘" subtitle="平台整体运营数据概览（近 7 天提交趋势）" />

    <div class="stat-grid">
      <StatCard
        label="用户总数"
        :value="data.user_total ?? '-'"
        :icon="User"
        color="#4f46e5"
        :hint="`其中管理员 ${data.admin_total ?? '-'} 名`"
      />
      <StatCard label="题目总数" :value="data.problem_total ?? '-'" :icon="Notebook" color="#0ea5e9" />
      <StatCard label="提交总数" :value="data.submission_total ?? '-'" :icon="Upload" color="#f59e0b" />
      <StatCard label="通过率" :value="acceptRate" :icon="TrendCharts" color="#10b981" />
    </div>

    <el-row :gutter="16">
      <!-- 状态分布 -->
      <el-col :xs="24" :md="10">
        <el-card header="判题状态分布" shadow="never">
          <div v-for="(v, k) in statusOptions" :key="k" class="dist-row">
            <VerdictBadge :status="k" />
            <el-progress
              :percentage="distPercent(v)"
              :stroke-width="14"
              style="flex: 1; margin-left: 12px"
            />
            <span class="dist-count">{{ v }}</span>
          </div>
          <EmptyState v-if="!distTotal" description="暂无提交数据" />
        </el-card>
      </el-col>

      <!-- 近 7 天提交趋势 -->
      <el-col :xs="24" :md="14">
        <el-card header="近 7 天提交趋势" shadow="never">
          <div class="trend">
            <div v-for="item in trendData" :key="item.date" class="trend-row">
              <span class="trend-date">{{ item.date }}</span>
              <el-progress
                :percentage="trendPercent(item.count)"
                :stroke-width="16"
                style="flex: 1"
              />
              <span class="dist-count">{{ item.count }}</span>
            </div>
            <EmptyState v-if="!trendData.length" description="近 7 天暂无提交" />
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Notebook, TrendCharts, Upload, User } from '@element-plus/icons-vue'
import { fetchDashboard } from '@/api/admin'
import { VERDICT_MAP } from '@/utils/verdict'
import VerdictBadge from '@/components/VerdictBadge.vue'
import PageHeader from '@/components/PageHeader.vue'
import StatCard from '@/components/StatCard.vue'
import EmptyState from '@/components/EmptyState.vue'

const data = ref({})
const loading = ref(false)

const statusOptions = computed(() =>
  Object.fromEntries(
    Object.entries(data.value.status_distribution || {}).filter(
      ([k]) => VERDICT_MAP[k] && k !== 'pending'
    )
  )
)
const distTotal = computed(() =>
  Object.values(statusOptions.value).reduce((a, b) => a + b, 0)
)
const distPercent = (v) =>
  distTotal.value ? Math.round((v / distTotal.value) * 100) : 0

const trendData = computed(() => data.value.submission_trend_7d || [])
const trendMax = computed(() => Math.max(1, ...trendData.value.map((t) => t.count)))
const trendPercent = (c) => Math.round((c / trendMax.value) * 100)

const acceptRate = computed(() => {
  const accepted = statusOptions.value.accepted || 0
  return distTotal.value ? `${Math.round((accepted / distTotal.value) * 100)}%` : '-'
})

onMounted(async () => {
  loading.value = true
  try {
    const { data: d } = await fetchDashboard()
    data.value = d
  } catch (e) {
    ElMessage.error(e.message || '加载失败')
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}
.dist-row,
.trend-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
.dist-count {
  width: 48px;
  text-align: right;
  color: var(--c-text-regular);
  font-size: 13px;
}
.trend-date {
  width: 92px;
  color: var(--c-text-regular);
  font-size: 12px;
}
</style>
