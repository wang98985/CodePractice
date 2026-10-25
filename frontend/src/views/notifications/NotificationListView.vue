<template>
  <div>
    <PageHeader title="通知中心" subtitle="讨论回复与系统消息都会汇总在这里">
      <template #actions>
        <el-button :disabled="!unreadCount" @click="readAll">全部标为已读</el-button>
      </template>
    </PageHeader>

    <el-card shadow="never">
      <el-tabs v-model="filter" @tab-change="load(1)">
        <el-tab-pane label="全部" name="all" />
        <el-tab-pane :label="`未读（${unreadCount}）`" name="unread" />
      </el-tabs>

      <div v-loading="loading" class="notice-list">
        <div
          v-for="n in rows"
          :key="n.id"
          class="notice-item"
          :class="{ 'is-unread': !n.is_read }"
          @click="open(n)"
        >
          <span v-if="!n.is_read" class="notice-dot" />
          <div class="notice-main">
            <div class="notice-head">
              <span class="notice-title">{{ n.title }}</span>
              <el-tag size="small" effect="plain" type="info">{{ n.kind_display }}</el-tag>
            </div>
            <p v-if="n.content" class="notice-content">{{ n.content }}</p>
            <div class="notice-meta">
              <span>{{ formatTime(n.created_at) }}</span>
              <el-link v-if="n.link" type="primary" :underline="false">查看详情</el-link>
            </div>
          </div>
          <el-button link type="danger" size="small" class="notice-del" @click.stop="remove(n)">
            删除
          </el-button>
        </div>

        <p v-if="!loading && !rows.length" class="text-muted notice-empty">
          {{ filter === 'unread' ? '没有未读通知' : '暂时还没有通知' }}
        </p>
      </div>

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
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  removeNotification,
} from '@/api/notifications'
import PageHeader from '@/components/PageHeader.vue'

const router = useRouter()
const rows = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const filter = ref('all')
const unreadCount = ref(0)

function formatTime(t) {
  return t ? new Date(t).toLocaleString('zh-CN', { hour12: false }) : '-'
}

async function load(p = 1) {
  page.value = p
  loading.value = true
  try {
    const params = { page: p, page_size: pageSize.value }
    if (filter.value === 'unread') params.unread = 1
    const { data } = await listNotifications(params)
    rows.value = data.results
    total.value = data.count
    if (!filter.value || filter.value === 'all') {
      unreadCount.value = data.results.filter((n) => !n.is_read).length
    }
    if (!data.results.length && p > 1) {
      await load(p - 1)
    }
  } catch (e) {
    ElMessage.error(e.message || '通知加载失败')
  } finally {
    loading.value = false
  }
}

async function refreshUnread() {
  const { data } = await listNotifications({ unread: 1, page_size: 1 })
  unreadCount.value = data.count
}

async function open(n) {
  if (!n.is_read) {
    try {
      await markNotificationRead(n.id)
      n.is_read = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    } catch {
      /* 标记失败不阻塞跳转 */
    }
  }
  if (n.link) router.push(n.link)
}

async function readAll() {
  try {
    await markAllNotificationsRead()
    ElMessage.success('已全部标为已读')
    load(page.value)
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  }
}

async function remove(n) {
  try {
    await ElMessageBox.confirm('确定删除这条通知吗？', '删除通知', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await removeNotification(n.id)
    ElMessage.success('已删除')
    load(page.value)
  } catch (e) {
    ElMessage.error(e.message || '删除失败')
  }
}

onMounted(() => {
  load(1)
  refreshUnread()
})
</script>

<style scoped>
.notice-list {
  min-height: 80px;
}
.notice-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 14px 4px;
  border-bottom: 1px solid var(--c-border-light);
  cursor: pointer;
  transition: background-color 0.15s ease;
}
.notice-item:hover {
  background: var(--c-bg);
}
.notice-item.is-unread .notice-title {
  font-weight: 600;
}
.notice-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--brand-500);
  margin-top: 7px;
  flex: none;
}
.notice-main {
  flex: 1;
  min-width: 0;
}
.notice-head {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.notice-title {
  font-size: 14px;
  color: var(--c-text);
}
.notice-content {
  margin: 6px 0 0;
  font-size: 13px;
  color: var(--c-text-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.notice-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 6px;
  font-size: 12px;
  color: var(--c-text-secondary);
}
.notice-del {
  flex: none;
}
.notice-empty {
  padding: 24px 0;
  font-size: 14px;
}
</style>
