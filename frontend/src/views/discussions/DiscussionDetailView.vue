<template>
  <div v-loading="loading">
    <PageHeader :title="disc.title || '讨论详情'" :subtitle="disc.problem_title || ''">
      <template #actions>
        <el-button v-if="disc.problem_id" @click="$router.push(`/problems/${disc.problem_id}`)">
          返回题目
        </el-button>
      </template>
    </PageHeader>

    <el-card v-if="!loading" shadow="never" class="disc-card">
      <div class="disc-head">
        <div class="disc-head__main">
          <el-tag v-if="disc.is_solution" type="success" effect="plain" size="small">题解</el-tag>
          <el-tag v-else type="info" effect="plain" size="small">讨论</el-tag>
          <span class="text-muted">{{ disc.author_nickname }}</span>
          <span class="text-muted">· {{ formatTime(disc.created_at) }}</span>
        </div>
        <el-button v-if="canDelete" link type="danger" size="small" @click="removeDiscussion">
          删除
        </el-button>
      </div>

      <h2 class="disc-title">{{ disc.title }}</h2>
      <MarkdownView :content="disc.content || ''" />
    </el-card>

    <el-card v-if="!loading" shadow="never" class="replies-card">
      <div class="replies-head">回复（{{ disc.replies?.length || 0 }}）</div>

      <div v-if="!disc.replies?.length" class="text-muted empty-replies">还没有回复，来抢第一个沙发</div>

      <div v-for="r in disc.replies" :key="r.id" class="reply-item">
        <div class="reply-head">
          <span class="reply-author">{{ r.author_nickname }}</span>
          <span class="text-muted">{{ formatTime(r.created_at) }}</span>
          <el-button
            v-if="canDeleteReply(r)"
            link
            type="danger"
            size="small"
            @click="removeReply(r)"
          >
            删除
          </el-button>
        </div>
        <MarkdownView :content="r.content || ''" />
      </div>

      <div class="reply-editor">
        <el-input
          v-model="replyContent"
          type="textarea"
          :rows="4"
          maxlength="5000"
          show-word-limit
          placeholder="支持 Markdown，理性讨论更有帮助"
        />
        <el-button type="primary" :loading="replying" @click="submitReply">发表回复</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createReply, deleteDiscussion, deleteReply, getDiscussion } from '@/api/discussions'
import { useAuthStore } from '@/stores/auth'
import PageHeader from '@/components/PageHeader.vue'
import MarkdownView from '@/components/MarkdownView.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const disc = ref({})
const loading = ref(true)
const replyContent = ref('')
const replying = ref(false)

const canDelete = computed(
  () => auth.isAdmin || disc.value.author_id === auth.user?.id
)

function canDeleteReply(r) {
  return auth.isAdmin || r.author_id === auth.user?.id
}

function formatTime(t) {
  return t ? new Date(t).toLocaleString('zh-CN', { hour12: false }) : '-'
}

async function load() {
  loading.value = true
  try {
    const { data } = await getDiscussion(route.params.id)
    disc.value = data
  } catch (e) {
    ElMessage.error(e.message || '讨论加载失败')
  } finally {
    loading.value = false
  }
}

async function submitReply() {
  if (!replyContent.value.trim()) {
    ElMessage.warning('回复内容不能为空')
    return
  }
  replying.value = true
  try {
    await createReply(disc.value.id, replyContent.value.trim())
    replyContent.value = ''
    ElMessage.success('回复成功')
    load()
  } catch (e) {
    ElMessage.error(e.message || '回复失败')
  } finally {
    replying.value = false
  }
}

async function removeDiscussion() {
  try {
    await ElMessageBox.confirm('删除后讨论及其回复将不可恢复，确定删除吗？', '删除讨论', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await deleteDiscussion(disc.value.id)
    ElMessage.success('已删除')
    router.push(`/problems/${disc.value.problem_id}`)
  } catch (e) {
    ElMessage.error(e.message || '删除失败')
  }
}

async function removeReply(r) {
  try {
    await ElMessageBox.confirm('确定删除这条回复吗？', '删除回复', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await deleteReply(r.id)
    ElMessage.success('已删除')
    load()
  } catch (e) {
    ElMessage.error(e.message || '删除失败')
  }
}

onMounted(load)
</script>

<style scoped>
.disc-card,
.replies-card {
  margin-bottom: 16px;
}
.disc-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}
.disc-head__main {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  font-size: 13px;
}
.disc-title {
  font-size: 20px;
  margin: 4px 0 12px;
}
.replies-head {
  font-weight: 600;
  margin-bottom: 12px;
}
.empty-replies {
  font-size: 14px;
  padding: 8px 0 16px;
}
.reply-item {
  border-top: 1px solid var(--c-border-light);
  padding: 12px 0;
}
.reply-head {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  margin-bottom: 6px;
}
.reply-author {
  font-weight: 600;
}
.reply-editor {
  border-top: 1px solid var(--c-border-light);
  padding-top: 16px;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 12px;
}
</style>
