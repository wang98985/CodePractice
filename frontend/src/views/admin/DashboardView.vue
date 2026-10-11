<template>
  <div v-loading="loading">
    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-label">用户总数</div>
          <div class="stat-value">{{ data.user_total ?? '-' }}</div>
          <div class="stat-sub">其中管理员 {{ data.admin_total ?? '-' }} 名</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-label">题目总数</div>
          <div class="stat-value">{{ data.problem_total ?? '-' }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-label">提交总数</div>
          <div class="stat-value">{{ data.submission_total ?? '-' }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-label">通过率</div>
          <div class="stat-value">{{ acceptRate }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <!-- 状态分布 -->
      <el-col :span="10">
        <el-card header="判题状态分布">
          <div v-for="(v, k) in statusOptions" :key="k" class="dist-row">
            <VerdictBadge :status="k" />
            <el-progress
              :percentage="distPercent(v)"
              :stroke-width="14"
              style="flex: 1; margin-left: 12px"
            />
            <span class="dist-count">{{ v }}</span>
          </div>
          <el-empty v-if="!distTotal" description="暂无提交数据" :image-size="60" />
        </el-card>
      </el-col>

      <!-- 近 7 天提交趋势 -->
      <el-col :span="14">
        <el-card header="近 7 天提交趋势">
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
            <el-empty v-if="!trendData.length" description="近 7 天暂无提交" :image-size="60" />
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchDashboard } from '@/api/admin'
import { VERDICT_MAP } from '@/utils/verdict'
import VerdictBadge from '@/components/VerdictBadge.vue'

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
.stat-row {
  margin-bottom: 16px;
}
.stat-label {
  color: #909399;
  font-size: 13px;
}
.stat-value {
  font-size: 28px;
  font-weight: 700;
  margin: 4px 0;
}
.stat-sub {
  color: #c0c4cc;
  font-size: 12px;
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
  color: #606266;
  font-size: 13px;
}
.trend-date {
  width: 92px;
  color: #606266;
  font-size: 12px;
}
</style>
