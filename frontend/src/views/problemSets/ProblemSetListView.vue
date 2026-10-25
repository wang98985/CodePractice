<template>
  <div>
    <PageHeader title="题单" subtitle="把想练的题目整理成清单，按进度逐题攻克">
      <template #actions>
        <el-button type="primary" @click="openCreate">新建题单</el-button>
      </template>
    </PageHeader>

    <div v-loading="loading" class="list-cards">
      <router-link
        v-for="set in sets"
        :key="set.id"
        :to="`/problem-sets/${set.id}`"
        class="list-card is-link set-card"
      >
        <div class="set-card__head">
          <span class="set-card__title">{{ set.title }}</span>
          <el-tag size="small" type="info" effect="plain">{{ set.problem_count }} 题</el-tag>
        </div>
        <p class="set-card__desc">{{ set.description || '暂无描述' }}</p>
        <el-progress
          :percentage="progress(set)"
          :stroke-width="6"
          :show-text="false"
          :color="progress(set) === 100 && set.problem_count ? '#34c759' : '#0071e3'"
        />
        <div class="set-card__meta">
          <span>已通过 {{ set.solved_count }} / {{ set.problem_count }}</span>
          <span>{{ formatTime(set.updated_at) }} 更新</span>
        </div>
      </router-link>

      <el-empty v-if="!loading && !sets.length" description="还没有题单，创建一个开始整理练习计划" />
    </div>

    <el-dialog v-model="dialogVisible" title="新建题单" width="480px" :close-on-click-modal="false">
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="题单名称" prop="title">
          <el-input v-model="form.title" maxlength="100" show-word-limit placeholder="例如：动态规划入门" />
        </el-form-item>
        <el-form-item label="描述（选填）">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            maxlength="500"
            show-word-limit
            placeholder="简单说明这个题单的目标"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submit">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { createProblemSet, listProblemSets } from '@/api/problemSets'
import PageHeader from '@/components/PageHeader.vue'

const router = useRouter()
const sets = ref([])
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const formRef = ref(null)
const form = reactive({ title: '', description: '' })
const rules = { title: [{ required: true, message: '请输入题单名称', trigger: 'blur' }] }

function progress(set) {
  if (!set.problem_count) return 0
  return Math.round((set.solved_count / set.problem_count) * 100)
}

function formatTime(t) {
  return t ? new Date(t).toLocaleDateString('zh-CN') : '-'
}

async function load() {
  loading.value = true
  try {
    const { data } = await listProblemSets()
    sets.value = data
  } catch (e) {
    ElMessage.error(e.message || '加载失败')
  } finally {
    loading.value = false
  }
}

function openCreate() {
  form.title = ''
  form.description = ''
  dialogVisible.value = true
}

async function submit() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  saving.value = true
  try {
    const { data } = await createProblemSet({ ...form })
    ElMessage.success('题单已创建')
    dialogVisible.value = false
    router.push(`/problem-sets/${data.id}`)
  } catch (e) {
    ElMessage.error(e.message || '创建失败')
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.set-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}
.set-card__title {
  font-size: 16px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.set-card__desc {
  margin: 6px 0 14px;
  font-size: 13px;
  color: var(--c-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.set-card__meta {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
  font-size: 12px;
  color: var(--c-text-secondary);
}
</style>
