<template>
  <div>
    <PageHeader title="排行榜" subtitle="按通过题目数排名，记录每个人的练习成果" />

    <!-- 我的排名 -->
    <div v-if="me" class="my-rank">
      <div class="my-rank__rank">
        <span class="my-rank__label">我的排名</span>
        <span class="my-rank__value">{{ me.rank }}</span>
        <span class="my-rank__unit">/ {{ total }}</span>
      </div>
      <div class="my-rank__stats">
        <div class="my-rank__stat">
          <span class="my-rank__num">{{ me.solved_count }}</span>
          <span class="my-rank__name">通过题目</span>
        </div>
        <div class="my-rank__stat">
          <span class="my-rank__num">{{ me.accepted_count }}</span>
          <span class="my-rank__name">通过提交</span>
        </div>
        <div class="my-rank__stat">
          <span class="my-rank__num">{{ me.accuracy }}%</span>
          <span class="my-rank__name">通过率</span>
        </div>
      </div>
    </div>
    <div v-else class="my-rank is-empty">
      <span>你还没有提交记录，提交一次代码即可参与排名</span>
    </div>

    <el-card shadow="never">
      <el-table v-if="!isMobile" v-loading="loading" :data="rows" stripe>
        <el-table-column label="排名" width="90">
          <template #default="{ row }">
            <span v-if="row.rank <= 3" class="medal" :class="`medal-${row.rank}`">{{ row.rank }}</span>
            <span v-else class="rank-num">{{ row.rank }}</span>
          </template>
        </el-table-column>
        <el-table-column label="用户" min-width="200">
          <template #default="{ row }">
            <div class="user-cell">
              <UserAvatar :name="row.nickname" :size="30" />
              <router-link :to="`/users/${row.user_id}`" class="user-name">{{ row.nickname }}</router-link>
              <el-tag v-if="row.user_id === auth.user?.id" size="small" type="primary" effect="plain">我</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="通过题目" width="110" align="center">
          <template #default="{ row }">
            <span class="solved">{{ row.solved_count }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="accepted_count" label="通过提交" width="110" align="center" />
        <el-table-column prop="total_submissions" label="提交总数" width="110" align="center" />
        <el-table-column label="通过率" width="120" align="center">
          <template #default="{ row }">{{ row.accuracy }}%</template>
        </el-table-column>
      </el-table>

      <!-- 手机端：卡片列表替代表格 -->
      <div v-else v-loading="loading" class="list-cards">
        <div v-for="row in rows" :key="row.user_id" class="list-card">
          <div class="list-card__head">
            <div class="user-cell">
              <span v-if="row.rank <= 3" class="medal" :class="`medal-${row.rank}`">{{ row.rank }}</span>
              <span v-else class="rank-num">{{ row.rank }}</span>
              <UserAvatar :name="row.nickname" :size="26" />
              <router-link :to="`/users/${row.user_id}`" class="user-name">{{ row.nickname }}</router-link>
            </div>
            <el-tag v-if="row.user_id === auth.user?.id" size="small" type="primary" effect="plain">我</el-tag>
          </div>
          <div class="list-card__meta">
            <span class="list-card__aux">通过题目 {{ row.solved_count }}</span>
            <span class="list-card__aux">通过提交 {{ row.accepted_count }}</span>
            <span class="list-card__aux">提交 {{ row.total_submissions }}</span>
            <span class="list-card__aux">通过率 {{ row.accuracy }}%</span>
          </div>
        </div>
        <p v-if="!loading && !rows.length" class="text-muted">暂无排名数据</p>
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
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getLeaderboard } from '@/api/leaderboard'
import { useAuthStore } from '@/stores/auth'
import { useIsMobile } from '@/composables/useResponsive'
import PageHeader from '@/components/PageHeader.vue'
import UserAvatar from '@/components/UserAvatar.vue'

const auth = useAuthStore()
const isMobile = useIsMobile()
const rows = ref([])
const me = ref(null)
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)

async function load(p = 1) {
  page.value = p
  loading.value = true
  try {
    const { data } = await getLeaderboard({ page: p })
    rows.value = data.results
    total.value = data.count
    me.value = data.me
    pageSize.value = data.page_size
  } catch (e) {
    ElMessage.error(e.message || '加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => load(1))
</script>

<style scoped>
.my-rank {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  flex-wrap: wrap;
  padding: 18px 22px;
  margin-bottom: 18px;
  background: var(--c-surface);
  border: 1px solid var(--c-border-light);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-1);
}
.my-rank__rank {
  display: flex;
  align-items: baseline;
  gap: 6px;
}
.my-rank__label {
  font-size: 13px;
  color: var(--c-text-secondary);
}
.my-rank__value {
  font-size: 32px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--brand-500);
}
.my-rank__unit {
  font-size: 13px;
  color: var(--c-text-secondary);
}
.my-rank__stats {
  display: flex;
  gap: 32px;
}
.my-rank__stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}
.my-rank__num {
  font-size: 18px;
  font-weight: 600;
  color: var(--c-text);
}
.my-rank__name {
  font-size: 12px;
  color: var(--c-text-secondary);
}
.my-rank.is-empty {
  justify-content: center;
  color: var(--c-text-secondary);
  font-size: 14px;
}

.medal {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  font-size: 13px;
  font-weight: 700;
  color: #fff;
}
.medal-1 {
  background: linear-gradient(135deg, #f7c948, #d9a300);
}
.medal-2 {
  background: linear-gradient(135deg, #c7ccd4, #8f959f);
}
.medal-3 {
  background: linear-gradient(135deg, #e2a06a, #b5713a);
}
.rank-num {
  display: inline-block;
  width: 26px;
  text-align: center;
  color: var(--c-text-secondary);
  font-weight: 500;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.user-name {
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.solved {
  font-weight: 700;
  color: var(--brand-500);
}

@media (max-width: 560px) {
  .my-rank {
    padding: 16px;
  }
  .my-rank__stats {
    width: 100%;
    justify-content: space-between;
    gap: 8px;
  }
  .my-rank__value {
    font-size: 26px;
  }
}
</style>
