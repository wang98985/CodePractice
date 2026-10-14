<template>
  <div class="assistant-fab">
    <!-- 悬浮面板 -->
    <el-card v-show="store.open" class="assistant-panel" shadow="always">
      <template #header>
        <div class="panel-header">
          <span>AI 助理</span>
          <div>
            <el-select
              v-model="currentSessionId"
              size="small"
              placeholder="历史会话"
              style="width: 140px; margin-right: 8px"
              clearable
              @change="loadSession"
            >
              <el-option
                v-for="s in sessions"
                :key="s.id"
                :value="s.id"
                :label="s.title.slice(0, 12)"
              />
            </el-select>
            <el-button size="small" @click="newChat">新对话</el-button>
            <el-button size="small" text @click="store.toggle(false)">
              <el-icon><Close /></el-icon>
            </el-button>
          </div>
        </div>
      </template>

      <div v-if="store.problemContext" class="problem-chip">
        <el-tag size="small" type="primary" effect="plain">
          关联题目：{{ store.problemContext.title }}
        </el-tag>
        <el-link type="info" :underline="false" @click="store.clearProblem()">移除</el-link>
      </div>

      <div ref="messageList" class="message-list">
        <div
          v-for="(m, i) in messages"
          :key="i"
          class="message-item"
          :class="m.role"
        >
          <div v-if="m.role === 'assistant'" class="bubble assistant-bubble">
            <MarkdownView :content="m.content" />
          </div>
          <div v-else class="bubble user-bubble">{{ m.content }}</div>
        </div>
        <EmptyState
          v-if="!messages.length"
          description="向 AI 助理提问，例如：这道题的思路是什么？"
        />
      </div>

      <div class="input-row">
        <el-input
          v-model="draft"
          type="textarea"
          :rows="2"
          placeholder="输入问题…（Enter 发送）"
          :disabled="sending"
          @keydown.enter.exact.prevent="send"
        />
        <el-button type="primary" :loading="sending" @click="send">发送</el-button>
      </div>
    </el-card>

    <!-- 悬浮按钮 -->
    <el-button
      type="primary"
      circle
      size="large"
      class="fab-button"
      @click="store.toggle()"
    >
      <el-icon :size="22"><ChatDotRound /></el-icon>
    </el-button>
  </div>
</template>

<script setup>
import { nextTick, onMounted, ref } from 'vue'
import { ChatDotRound, Close } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import {
  fetchSessionMessages,
  listSessions,
  streamChat,
} from '@/api/assistant'
import { useAssistantStore } from '@/stores/assistant'
import MarkdownView from '@/components/MarkdownView.vue'
import EmptyState from '@/components/EmptyState.vue'

const store = useAssistantStore()
const sessions = ref([])
const currentSessionId = ref(null)
const messages = ref([])
const draft = ref('')
const sending = ref(false)
const messageList = ref(null)

onMounted(loadSessions)

async function loadSessions() {
  try {
    const { data } = await listSessions({ page_size: 50 })
    sessions.value = data.results || data
  } catch { /* ignore */ }
}

async function loadSession(id) {
  if (!id) return
  try {
    const { data } = await fetchSessionMessages(id)
    messages.value = (data.results || data).map((m) => ({ role: m.role, content: m.content }))
  } catch (e) {
    ElMessage.error(e.message || '加载会话失败')
  }
}

function newChat() {
  currentSessionId.value = null
  messages.value = []
}

function scrollToBottom() {
  nextTick(() => {
    messageList.value?.scrollTo({ top: messageList.value.scrollHeight })
  })
}

async function send() {
  const text = draft.value.trim()
  if (!text || sending.value) return
  draft.value = ''
  sending.value = true
  messages.value.push({ role: 'user', content: text })
  const assistantMsg = { role: 'assistant', content: '' }
  messages.value.push(assistantMsg)
  scrollToBottom()

  try {
    await streamChat(
      {
        session_id: currentSessionId.value || undefined,
        problem_id: store.problemContext?.id || undefined,
        message: text,
      },
      {
        onDelta: (delta) => {
          assistantMsg.content += delta
          scrollToBottom()
        },
        onNotice: (msg) => ElMessage.warning(msg),
        onError: (msg) => ElMessage.error(msg),
        onDone: () => {
          if (!assistantMsg.content) assistantMsg.content = '（无回复）'
        },
      }
    )
  } catch (e) {
    ElMessage.error(e.message || '发送失败')
    if (!assistantMsg.content) assistantMsg.content = '（请求失败）'
  } finally {
    sending.value = false
    scrollToBottom()
    loadSessions()
  }
}
</script>

<style scoped>
.assistant-fab {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 2000;
}
.fab-button {
  width: 52px;
  height: 52px;
  box-shadow: 0 6px 18px rgba(79, 70, 229, 0.42);
}
.assistant-panel {
  position: absolute;
  bottom: 64px;
  right: 0;
  width: 400px;
  height: 560px;
  display: flex;
  flex-direction: column;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-3);
}
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.problem-chip {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px;
}
.message-item {
  display: flex;
  margin-bottom: 10px;
}
.message-item.assistant {
  justify-content: flex-start;
}
.message-item.user {
  justify-content: flex-end;
}
.bubble {
  max-width: 85%;
  border-radius: var(--radius-md);
  padding: 8px 12px;
  font-size: 13px;
}
.assistant-bubble {
  background: var(--c-bg);
  border: 1px solid var(--c-border-light);
  width: 85%;
}
.user-bubble {
  background: var(--brand-gradient);
  color: #fff;
  white-space: pre-wrap;
}
.input-row {
  display: flex;
  gap: 8px;
  align-items: flex-end;
  padding-top: 8px;
  border-top: 1px solid var(--c-border-light);
}
</style>
