<template>
  <div v-loading="loading">
    <PageHeader title="成就徽章" subtitle="坚持练习解锁徽章，记录你的成长轨迹" />

    <el-card shadow="never" class="summary-card">
      <div class="summary-main">
        <div class="summary-num">
          <span class="summary-value">{{ summary.unlocked }}</span>
          <span class="summary-total">/ {{ summary.total }}</span>
        </div>
        <div class="summary-text">
          <div class="summary-title">已解锁徽章</div>
          <div class="text-muted summary-tip">
            {{ summary.unlocked === summary.total ? '全部成就已达成，太强了' : '继续刷题，解锁更多徽章' }}
          </div>
        </div>
      </div>
      <el-progress
        :percentage="percent"
        :stroke-width="10"
        :show-text="false"
        color="var(--brand-500)"
        class="summary-progress"
      />
    </el-card>

    <div v-for="group in groups" :key="group.name" class="badge-group">
      <div class="group-title">{{ group.name }}</div>
      <div class="badge-grid">
        <div
          v-for="a in group.items"
          :key="a.code"
          class="badge-card"
          :class="{ 'is-unlocked': a.unlocked }"
        >
          <div class="badge-icon">
            <el-icon :size="26"><component :is="iconOf(a.code)" /></el-icon>
          </div>
          <div class="badge-body">
            <div class="badge-head">
              <span class="badge-name">{{ a.name }}</span>
              <el-tag v-if="a.unlocked" size="small" type="success" effect="plain">已解锁</el-tag>
            </div>
            <p class="badge-desc">{{ a.description }}</p>
            <div v-if="a.unlocked" class="badge-meta">
              解锁于 {{ formatTime(a.unlocked_at) }}
            </div>
            <template v-else>
              <el-progress
                :percentage="progressPercent(a)"
                :stroke-width="6"
                :show-text="false"
                color="var(--brand-500)"
                class="badge-progress"
              />
              <div class="badge-meta">{{ Math.min(a.current, a.target) }} / {{ a.target }}</div>
            </template>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Aim, Checked, DataLine, Medal, Star, Timer, Trophy } from '@element-plus/icons-vue'
import { listAchievements } from '@/api/achievements'
import PageHeader from '@/components/PageHeader.vue'

const loading = ref(true)
const summary = ref({ unlocked: 0, total: 0 })
const achievements = ref([])

const ICONS = {
  first_ac: Aim,
  ac_10: Star,
  ac_50: Medal,
  ac_100: Trophy,
  submit_100: Timer,
  easy_ac: Checked,
  medium_ac: DataLine,
  hard_ac: Trophy,
}

const percent = computed(() =>
  summary.value.total ? Math.round((summary.value.unlocked / summary.value.total) * 100) : 0
)

const groups = computed(() => {
  const order = ['入门', '里程碑', '坚持', '难度']
  const map = new Map()
  for (const a of achievements.value) {
    if (!map.has(a.category)) map.set(a.category, [])
    map.get(a.category).push(a)
  }
  return order
    .filter((name) => map.has(name))
    .map((name) => ({ name, items: map.get(name) }))
})

function iconOf(code) {
  return ICONS[code] || Trophy
}

function progressPercent(a) {
  return a.target ? Math.min(100, Math.round((a.current / a.target) * 100)) : 0
}

function formatTime(t) {
  return t ? new Date(t).toLocaleString('zh-CN', { hour12: false }) : '-'
}

onMounted(async () => {
  try {
    const { data } = await listAchievements()
    summary.value = data.summary
    achievements.value = data.achievements
  } catch (e) {
    ElMessage.error(e.message || '成就加载失败')
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.summary-card {
  margin-bottom: 20px;
}
.summary-main {
  display: flex;
  align-items: center;
  gap: 16px;
}
.summary-num {
  display: flex;
  align-items: baseline;
  gap: 4px;
}
.summary-value {
  font-size: 34px;
  font-weight: 700;
  color: var(--brand-500);
  letter-spacing: -0.02em;
}
.summary-total {
  font-size: 15px;
  color: var(--c-text-secondary);
}
.summary-title {
  font-weight: 600;
}
.summary-tip {
  font-size: 13px;
  margin-top: 2px;
}
.summary-progress {
  margin-top: 14px;
}
.group-title {
  font-size: 15px;
  font-weight: 600;
  margin: 0 0 10px 2px;
}
.badge-group {
  margin-bottom: 20px;
}
.badge-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}
.badge-card {
  display: flex;
  gap: 14px;
  padding: 16px;
  border-radius: var(--radius-md);
  background: var(--c-surface);
  border: 1px solid var(--c-border-light);
  box-shadow: var(--shadow-1);
  opacity: 0.72;
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.badge-card.is-unlocked {
  opacity: 1;
  border-color: rgba(0, 113, 227, 0.22);
}
.badge-card.is-unlocked:hover {
  transform: translateY(-2px);
}
.badge-icon {
  width: 52px;
  height: 52px;
  flex: none;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--c-bg);
  color: var(--c-text-secondary);
}
.badge-card.is-unlocked .badge-icon {
  background: rgba(0, 113, 227, 0.1);
  color: var(--brand-500);
}
.badge-body {
  flex: 1;
  min-width: 0;
}
.badge-head {
  display: flex;
  align-items: center;
  gap: 8px;
}
.badge-name {
  font-weight: 600;
  font-size: 15px;
}
.badge-desc {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--c-text-secondary);
}
.badge-progress {
  margin-top: 8px;
}
.badge-meta {
  margin-top: 4px;
  font-size: 12px;
  color: var(--c-text-secondary);
}

@media (max-width: 560px) {
  .badge-grid {
    grid-template-columns: 1fr;
  }
}
</style>
