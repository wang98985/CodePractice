<template>
  <div v-loading="loading" class="profile-page">
    <PageHeader
      :title="isSelf ? '个人主页' : `${displayName} 的主页`"
      :subtitle="isSelf ? '查看你的练习数据与最近提交记录' : '该用户的练习数据与最近提交记录'"
    >
      <template #actions>
        <el-button v-if="isSelf" type="primary" @click="openEdit">
          <el-icon><Edit /></el-icon>
          <span>编辑资料</span>
        </el-button>
        <el-button @click="$router.push('/submissions')">我的提交</el-button>
      </template>
    </PageHeader>

    <div class="profile-grid">
      <!-- 左：资料卡 -->
      <el-card class="profile-card" shadow="never">
        <div class="profile-card__top">
          <UserAvatar :name="displayName" :size="76" />
          <div class="profile-card__name">
            <div class="name">{{ displayName }}</div>
            <div class="username">@{{ info.username || '-' }}</div>
            <el-tag size="small" effect="plain" :type="roleTagType">{{ roleText }}</el-tag>
          </div>
        </div>
        <p class="profile-card__bio">
          {{ info.bio || '这个人很懒，还没有填写个人简介' }}
        </p>
        <el-divider />
        <div class="meta-row">
          <span class="meta-label">加入时间</span>
          <span>{{ joinDate }}</span>
        </div>
        <div class="meta-row">
          <span class="meta-label">通过题目</span>
          <span>{{ stats.solved_count ?? 0 }} 题</span>
        </div>
      </el-card>

      <!-- 右：统计区 -->
      <div class="stat-area">
        <div class="stat-grid">
          <StatCard label="总提交" :value="stats.submission_total ?? 0" :icon="Upload" color="#4f46e5" />
          <StatCard label="通过提交" :value="stats.accepted_total ?? 0" :icon="CircleCheck" color="#10b981" />
          <StatCard label="通过题目" :value="stats.solved_count ?? 0" :icon="Medal" color="#f59e0b" />
          <StatCard label="尝试题目" :value="stats.attempted_count ?? 0" :icon="Aim" color="#8b5cf6" />
          <StatCard
            label="通过率"
            :value="`${stats.acceptance_rate ?? 0}%`"
            :icon="TrendCharts"
            color="#0ea5e9"
          />
        </div>

        <el-row :gutter="16" class="dist-area">
          <el-col :xs="24" :sm="12">
            <el-card header="难度分布（已通过）" shadow="never">
              <div class="diff-list">
                <div v-for="d in difficultyRows" :key="d.key" class="diff-row">
                  <span class="diff-name" :style="{ color: d.color }">{{ d.text }}</span>
                  <el-progress
                    :percentage="d.percent"
                    :stroke-width="12"
                    :show-text="false"
                    :color="d.color"
                    style="flex: 1"
                  />
                  <span class="diff-count">{{ d.count }}</span>
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-card header="语言分布" shadow="never">
              <div v-if="languageRows.length" class="lang-list">
                <div v-for="l in languageRows" :key="l.language" class="lang-row">
                  <el-tag size="small" effect="plain">{{ l.language }}</el-tag>
                  <el-progress
                    :percentage="l.percent"
                    :stroke-width="12"
                    :show-text="false"
                    style="flex: 1; margin: 0 10px"
                  />
                  <span class="lang-count">{{ l.count }}</span>
                </div>
              </div>
              <EmptyState v-else description="暂无提交记录" :icon-size="40" />
            </el-card>
          </el-col>
        </el-row>
      </div>
    </div>

    <!-- 最近提交 -->
    <el-card header="最近提交" shadow="never" class="recent-card">
      <el-table
        v-if="recent.length"
        :data="recent"
        stripe
        @row-click="(row) => $router.push(`/submissions/${row.id}`)"
      >
        <el-table-column label="题目" min-width="220">
          <template #default="{ row }">
            <el-link type="primary" underline="never" @click.stop="$router.push(`/problems/${row.problem.id}`)">
              {{ row.problem.title }}
            </el-link>
            <el-tag
              size="small"
              effect="plain"
              style="margin-left: 8px"
              :style="{ color: difficultyColor(row.problem.difficulty), borderColor: difficultyColor(row.problem.difficulty) }"
            >
              {{ difficultyText(row.problem.difficulty) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <VerdictBadge :status="row.status" />
          </template>
        </el-table-column>
        <el-table-column prop="language" label="语言" width="100" />
        <el-table-column label="耗时" width="100">
          <template #default="{ row }">{{ row.time_used_ms ? `${row.time_used_ms}ms` : '-' }}</template>
        </el-table-column>
        <el-table-column label="内存" width="110">
          <template #default="{ row }">
            {{ row.memory_used_kb ? `${Math.round(row.memory_used_kb / 1024)}MB` : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="提交时间" width="170">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
      </el-table>
      <EmptyState v-else :description="isSelf ? '你还没有提交过题目' : '该用户还没有提交记录'" />
    </el-card>

    <!-- 编辑资料 -->
    <el-dialog v-model="editVisible" title="编辑资料" width="440px">
      <el-form :model="form" label-width="76px">
        <el-form-item label="昵称">
          <el-input v-model="form.nickname" maxlength="32" show-word-limit placeholder="留空则显示用户名" />
        </el-form-item>
        <el-form-item label="个人简介">
          <el-input
            v-model="form.bio"
            type="textarea"
            :rows="3"
            maxlength="200"
            show-word-limit
            placeholder="介绍一下自己吧"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Aim, CircleCheck, Edit, Medal, TrendCharts, Upload } from '@element-plus/icons-vue'
import { fetchProfile } from '@/api/profile'
import { updateMe } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import { DIFFICULTY_MAP, difficultyColor, difficultyText } from '@/utils/verdict'
import PageHeader from '@/components/PageHeader.vue'
import StatCard from '@/components/StatCard.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import EmptyState from '@/components/EmptyState.vue'
import VerdictBadge from '@/components/VerdictBadge.vue'

const auth = useAuthStore()
const route = useRoute()

const info = ref({})
const stats = ref({})
const recent = ref([])
const loading = ref(false)
const editVisible = ref(false)
const saving = ref(false)
const form = reactive({ nickname: '', bio: '' })

const targetId = computed(() =>
  route.params.id ? Number(route.params.id) : auth.user?.id
)
const isSelf = computed(() => !!auth.user && targetId.value === auth.user.id)
const displayName = computed(() => info.value.nickname || info.value.username || '未知用户')
const roleText = computed(() => info.value.role_display || '普通用户')
const roleTagType = computed(
  () => ({ user: 'info', admin: 'warning', super_admin: 'danger' }[info.value.role] || 'info')
)
const joinDate = computed(() =>
  info.value.date_joined ? new Date(info.value.date_joined).toLocaleDateString('zh-CN') : '-'
)

const difficultyRows = computed(() => {
  const src = stats.value.difficulty_solved || {}
  const max = Math.max(1, ...Object.values(src), 0)
  return Object.entries(DIFFICULTY_MAP).map(([key, meta]) => ({
    key,
    text: meta.text,
    color: meta.color,
    count: src[key] ?? 0,
    percent: Math.round(((src[key] ?? 0) / max) * 100),
  }))
})

const languageRows = computed(() => {
  const list = stats.value.language_distribution || []
  const max = Math.max(1, ...list.map((i) => i.count), 0)
  return list.map((i) => ({ ...i, percent: Math.round((i.count / max) * 100) }))
})

function formatTime(ts) {
  if (!ts) return '-'
  return new Date(ts).toLocaleString('zh-CN', { hour12: false })
}

async function load() {
  if (!targetId.value) return
  loading.value = true
  try {
    const { data } = await fetchProfile(targetId.value)
    info.value = data.user
    stats.value = data.stats
    recent.value = data.recent_submissions || []
  } catch (e) {
    ElMessage.error(e.message || '加载失败')
  } finally {
    loading.value = false
  }
}

function openEdit() {
  form.nickname = info.value.nickname || ''
  form.bio = info.value.bio || ''
  editVisible.value = true
}

async function save() {
  saving.value = true
  try {
    await updateMe({ nickname: form.nickname, bio: form.bio })
    ElMessage.success('资料已更新')
    editVisible.value = false
    await auth.fetchMe()
    await load()
  } catch (e) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(load)
watch(targetId, load)
</script>

<style scoped>
.profile-grid {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 16px;
  align-items: start;
}
.profile-card__top {
  display: flex;
  align-items: center;
  gap: 16px;
}
.profile-card__name .name {
  font-size: 20px;
  font-weight: 700;
  color: var(--c-text);
}
.profile-card__name .username {
  font-size: 13px;
  color: var(--c-text-secondary);
  margin: 2px 0 6px;
}
.profile-card__bio {
  margin: 16px 0 0;
  font-size: 13px;
  color: var(--c-text-regular);
  line-height: 1.6;
}
.meta-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: var(--c-text-regular);
  padding: 4px 0;
}
.meta-label {
  color: var(--c-text-secondary);
}
.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 14px;
}
.dist-area {
  margin-top: 16px;
}
.diff-row,
.lang-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}
.diff-name {
  width: 40px;
  font-weight: 600;
  font-size: 13px;
}
.diff-count,
.lang-count {
  width: 40px;
  text-align: right;
  color: var(--c-text-regular);
  font-size: 13px;
}
.recent-card {
  margin-top: 16px;
}
@media (max-width: 900px) {
  .profile-grid {
    grid-template-columns: 1fr;
  }
}
</style>
