<template>
  <div v-loading="loading">
    <PageHeader :title="detail?.title || '题单'" :subtitle="detail?.description || ''">
      <template #actions>
        <el-button @click="$router.push('/problem-sets')">返回列表</el-button>
        <el-button @click="openEdit">编辑</el-button>
        <el-button type="primary" @click="openAdd">添加题目</el-button>
        <el-button type="danger" plain @click="removeSet">删除题单</el-button>
      </template>
    </PageHeader>

    <el-card shadow="never" class="overview">
      <div class="overview__progress">
        <span class="overview__label">完成进度</span>
        <el-progress
          :percentage="progress"
          :stroke-width="8"
          :color="progress === 100 && total ? '#34c759' : '#0071e3'"
          style="flex: 1"
        />
        <span class="overview__count">{{ detail?.solved_count || 0 }} / {{ total }}</span>
      </div>
    </el-card>

    <el-card v-if="!isMobile" shadow="never" style="margin-top: 16px">
      <el-table :data="detail?.items || []" stripe>
        <el-table-column prop="order" label="#" width="60" />
        <el-table-column label="题目" min-width="260">
          <template #default="{ row }">
            <el-link type="primary" underline="never" @click="$router.push(`/problems/${row.problem.id}`)">
              {{ row.problem.id }}. {{ row.problem.title }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column label="难度" width="100">
          <template #default="{ row }">
            <el-tag
              size="small"
              effect="plain"
              :style="{ color: difficultyColor(row.problem.difficulty), borderColor: difficultyColor(row.problem.difficulty) }"
            >
              {{ difficultyText(row.problem.difficulty) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag size="small" :type="row.accepted ? 'success' : 'info'" effect="plain">
              {{ row.accepted ? '已通过' : '未通过' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="danger" @click="removeItem(row)">移除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!detail?.items?.length" description="题单还没有题目，点击「添加题目」开始" />
    </el-card>

    <div v-else class="list-cards" style="margin-top: 16px">
      <div v-for="row in detail?.items || []" :key="row.id" class="list-card">
        <div class="list-card__head">
          <router-link :to="`/problems/${row.problem.id}`" class="list-card__title">
            {{ row.order }}. {{ row.problem.title }}
          </router-link>
          <el-button link type="danger" size="small" @click="removeItem(row)">移除</el-button>
        </div>
        <div class="list-card__meta">
          <el-tag
            size="small"
            effect="plain"
            :style="{ color: difficultyColor(row.problem.difficulty), borderColor: difficultyColor(row.problem.difficulty) }"
          >
            {{ difficultyText(row.problem.difficulty) }}
          </el-tag>
          <el-tag size="small" :type="row.accepted ? 'success' : 'info'" effect="plain">
            {{ row.accepted ? '已通过' : '未通过' }}
          </el-tag>
        </div>
      </div>
      <p v-if="!detail?.items?.length" class="text-muted">题单还没有题目，点击「添加题目」开始</p>
    </div>

    <!-- 编辑题单 -->
    <el-dialog v-model="editVisible" title="编辑题单" width="480px" :close-on-click-modal="false">
      <el-form ref="editFormRef" :model="editForm" :rules="rules" label-position="top">
        <el-form-item label="题单名称" prop="title">
          <el-input v-model="editForm.title" maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item label="描述（选填）">
          <el-input v-model="editForm.description" type="textarea" :rows="3" maxlength="500" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitEdit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 添加题目 -->
    <el-dialog v-model="addVisible" title="添加题目" width="560px" :close-on-click-modal="false">
      <el-input
        v-model="keyword"
        placeholder="搜索题目名称"
        clearable
        :prefix-icon="Search"
        @input="onSearch"
      />
      <div v-loading="searching" class="picker">
        <div v-for="p in candidates" :key="p.id" class="picker__row">
          <div class="picker__info">
            <span class="picker__title">{{ p.id }}. {{ p.title }}</span>
            <el-tag
              size="small"
              effect="plain"
              :style="{ color: difficultyColor(p.difficulty), borderColor: difficultyColor(p.difficulty) }"
            >
              {{ difficultyText(p.difficulty) }}
            </el-tag>
          </div>
          <el-button
            size="small"
            type="primary"
            plain
            :disabled="existingIds.has(p.id)"
            :loading="addingId === p.id"
            @click="addProblem(p)"
          >
            {{ existingIds.has(p.id) ? '已添加' : '添加' }}
          </el-button>
        </div>
        <p v-if="!searching && !candidates.length" class="text-muted">没有匹配的题目</p>
      </div>
      <template #footer>
        <el-button @click="addVisible = false">完成</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { listProblems } from '@/api/problems'
import {
  addProblemToSet,
  deleteProblemSet,
  getProblemSet,
  removeProblemFromSet,
  updateProblemSet,
} from '@/api/problemSets'
import { difficultyColor, difficultyText } from '@/utils/verdict'
import { useIsMobile } from '@/composables/useResponsive'
import PageHeader from '@/components/PageHeader.vue'

const route = useRoute()
const router = useRouter()
const isMobile = useIsMobile()

const detail = ref(null)
const loading = ref(false)
const saving = ref(false)
const setId = computed(() => route.params.id)

const total = computed(() => detail.value?.problem_count || 0)
const progress = computed(() =>
  total.value ? Math.round((detail.value.solved_count / total.value) * 100) : 0
)
const existingIds = computed(
  () => new Set((detail.value?.items || []).map((item) => item.problem.id))
)

async function load() {
  loading.value = true
  try {
    const { data } = await getProblemSet(setId.value)
    detail.value = data
  } catch (e) {
    ElMessage.error(e.message || '加载失败')
    router.push('/problem-sets')
  } finally {
    loading.value = false
  }
}

// ---- 编辑 ----
const editVisible = ref(false)
const editFormRef = ref(null)
const editForm = reactive({ title: '', description: '' })
const rules = { title: [{ required: true, message: '请输入题单名称', trigger: 'blur' }] }

function openEdit() {
  editForm.title = detail.value.title
  editForm.description = detail.value.description
  editVisible.value = true
}

async function submitEdit() {
  try {
    await editFormRef.value.validate()
  } catch {
    return
  }
  saving.value = true
  try {
    const { data } = await updateProblemSet(setId.value, { ...editForm })
    detail.value = data
    ElMessage.success('已保存')
    editVisible.value = false
  } catch (e) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function removeSet() {
  try {
    await ElMessageBox.confirm(`删除题单「${detail.value.title}」？题目本身不会被删除。`, '删除题单', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  try {
    await deleteProblemSet(setId.value)
    ElMessage.success('题单已删除')
    router.push('/problem-sets')
  } catch (e) {
    ElMessage.error(e.message || '删除失败')
  }
}

// ---- 添加题目 ----
const addVisible = ref(false)
const keyword = ref('')
const candidates = ref([])
const searching = ref(false)
const addingId = ref(null)
let searchTimer = null

async function searchProblems() {
  searching.value = true
  try {
    const { data } = await listProblems({ search: keyword.value, page_size: 20 })
    candidates.value = data.results
  } catch (e) {
    ElMessage.error(e.message || '搜索失败')
  } finally {
    searching.value = false
  }
}

function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(searchProblems, 300)
}

function openAdd() {
  addVisible.value = true
  keyword.value = ''
  searchProblems()
}

async function addProblem(problem) {
  addingId.value = problem.id
  try {
    await addProblemToSet(setId.value, problem.id)
    ElMessage.success('已添加到题单')
    await load()
  } catch (e) {
    ElMessage.error(e.message || '添加失败')
  } finally {
    addingId.value = null
  }
}

async function removeItem(row) {
  try {
    await removeProblemFromSet(setId.value, row.id)
    ElMessage.success('已移除')
    await load()
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  }
}

onMounted(load)
</script>

<style scoped>
.overview__progress {
  display: flex;
  align-items: center;
  gap: 16px;
}
.overview__label {
  font-size: 13px;
  color: var(--c-text-secondary);
  white-space: nowrap;
}
.overview__count {
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
}
.picker {
  max-height: 360px;
  overflow-y: auto;
  margin-top: 12px;
}
.picker__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 4px;
  border-bottom: 1px solid var(--c-border-light);
}
.picker__info {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.picker__title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
@media (max-width: 560px) {
  .overview__progress {
    flex-wrap: wrap;
    gap: 8px;
  }
}
</style>
