<template>
  <div>
    <PageHeader title="每日一题" subtitle="每天一道题，坚持练习保持手感" />

    <div v-loading="loading">
      <template v-if="today">
        <div class="daily-hero">
          <div class="daily-hero__meta">
            <span class="daily-hero__date">{{ formatDate(today.date) }}</span>
            <span class="daily-hero__weekday">{{ weekday(today.date) }}</span>
          </div>

          <h2 class="daily-hero__title" @click="$router.push(`/problems/${today.problem.id}`)">
            {{ today.problem.id }}. {{ today.problem.title }}
          </h2>

          <div class="daily-hero__tags">
            <el-tag
              size="small"
              effect="plain"
              :style="{
                color: difficultyColor(today.problem.difficulty),
                borderColor: difficultyColor(today.problem.difficulty),
              }"
            >
              {{ difficultyText(today.problem.difficulty) }}
            </el-tag>
            <el-tag v-for="t in today.problem.tags" :key="t.id" size="small" type="info" effect="plain">
              {{ t.name }}
            </el-tag>
          </div>

          <div class="daily-hero__actions">
            <el-button type="primary" size="large" @click="$router.push(`/problems/${today.problem.id}`)">
              {{ today.accepted ? '再做一次' : '开始作答' }}
            </el-button>
            <span v-if="today.accepted" class="state state--done">
              <el-icon><CircleCheckFilled /></el-icon> 今日已通过
            </span>
            <span v-else-if="today.submitted" class="state state--pending">今日已提交，尚未通过</span>
            <span v-else class="state">今日还未提交</span>
          </div>
        </div>

        <h3 class="section-title">最近 6 天</h3>
        <div class="list-cards history">
          <div v-for="row in recent" :key="row.date" class="list-card history__row">
            <div class="history__date">
              <span class="history__day">{{ formatDate(row.date) }}</span>
              <span class="history__weekday">{{ weekday(row.date) }}</span>
            </div>
            <router-link :to="`/problems/${row.problem.id}`" class="history__title">
              {{ row.problem.title }}
            </router-link>
            <el-tag size="small" :type="row.accepted ? 'success' : 'info'" effect="plain">
              {{ row.accepted ? '已通过' : '未通过' }}
            </el-tag>
          </div>
          <p v-if="!recent.length" class="text-muted">暂无历史记录</p>
        </div>
      </template>

      <el-empty v-else-if="!loading" description="题库还没有公开题目，暂时无法生成每日一题" />
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { CircleCheckFilled } from '@element-plus/icons-vue'
import { getDailyProblem } from '@/api/daily'
import { difficultyColor, difficultyText } from '@/utils/verdict'
import PageHeader from '@/components/PageHeader.vue'

const today = ref(null)
const recent = ref([])
const loading = ref(false)

const WEEKDAYS = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']

function formatDate(iso) {
  const [, m, d] = iso.split('-')
  return `${Number(m)} 月 ${Number(d)} 日`
}

function weekday(iso) {
  return WEEKDAYS[new Date(`${iso}T00:00:00`).getDay()]
}

async function load() {
  loading.value = true
  try {
    const { data } = await getDailyProblem()
    today.value = data.today
    recent.value = data.recent || []
  } catch (e) {
    ElMessage.error(e.message || '加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.daily-hero {
  padding: 28px 30px;
  background: var(--c-surface);
  border: 1px solid var(--c-border-light);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-1);
}
.daily-hero__meta {
  display: flex;
  align-items: baseline;
  gap: 8px;
  color: var(--c-text-secondary);
  font-size: 13px;
}
.daily-hero__date {
  font-weight: 600;
  color: var(--brand-500);
}
.daily-hero__title {
  margin: 10px 0 12px;
  font-size: 26px;
  font-weight: 700;
  letter-spacing: -0.02em;
  cursor: pointer;
}
.daily-hero__title:hover {
  color: var(--brand-500);
}
.daily-hero__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 22px;
}
.daily-hero__actions {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}
.state {
  font-size: 13px;
  color: var(--c-text-secondary);
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.state--done {
  color: #34c759;
}
.state--pending {
  color: #ff9500;
}

.section-title {
  margin: 28px 0 12px;
  font-size: 16px;
  font-weight: 600;
}
.history {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.history__row {
  display: flex;
  align-items: center;
  gap: 14px;
}
.history__date {
  display: flex;
  flex-direction: column;
  min-width: 84px;
}
.history__day {
  font-size: 14px;
  font-weight: 600;
}
.history__weekday {
  font-size: 12px;
  color: var(--c-text-secondary);
}
.history__title {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 500;
}

@media (max-width: 560px) {
  .daily-hero {
    padding: 20px;
  }
  .daily-hero__title {
    font-size: 20px;
  }
  .history__row {
    align-items: flex-start;
    flex-wrap: wrap;
    gap: 8px;
  }
}
</style>
