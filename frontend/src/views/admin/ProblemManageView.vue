<template>
  <el-card>
    <div class="toolbar">
      <el-button type="primary" @click="openCreate">新建题目</el-button>
      <el-button v-if="auth.isSuperAdmin" type="success" @click="importVisible = true">批量导入</el-button>
      <el-button @click="load">刷新</el-button>
    </div>

    <el-table v-loading="loading" :data="rows" stripe>
      <el-table-column prop="id" label="ID" width="64" />
      <el-table-column prop="title" label="标题" min-width="220" />
      <el-table-column label="难度" width="90">
        <template #default="{ row }">
          <span :style="{ color: difficultyColor(row.difficulty) }">{{ difficultyText(row.difficulty) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="标签" min-width="140">
        <template #default="{ row }">
          <el-tag v-for="t in row.tags" :key="t.id" size="small" type="info" effect="plain" style="margin-right: 4px">
            {{ t.name }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="用例数" prop="test_case_count" width="80" />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.is_public ? 'success' : 'info'" size="small">
            {{ row.is_public ? '已公开' : '未公开' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" @click="openCases(row)">用例</el-button>
          <el-button size="small" type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="page"
      v-model:page-size="pageSize"
      :total="total"
      :page-sizes="[20, 50, 100, 200]"
      layout="total, sizes, prev, pager, next, jumper"
      class="pager"
      @size-change="onPageSizeChange"
      @current-change="load"
    />
  </el-card>

  <!-- 批量导入对话框（仅超管） -->
  <el-dialog v-model="importVisible" title="批量导入题目" width="780px" top="4vh">
    <el-alert type="info" :closable="false" show-icon class="import-alert">
      支持 CSV（含表头，Excel 可直接编辑）或 JSON 数组；可粘贴文本，也可上传 .csv / .txt / .json 文件。
      多组示例/隐藏用例用 ||| 分隔；导入后默认未公开，可在列表中逐题修改。
    </el-alert>
    <el-tabs v-model="importTab">
      <el-tab-pane label="粘贴文本" name="text">
        <el-input v-model="importText" type="textarea" :rows="10" placeholder="粘贴 CSV（第一行为表头）或 JSON 数组" />
      </el-tab-pane>
      <el-tab-pane label="上传文件" name="file">
        <el-upload
          drag
          accept=".csv,.txt,.json"
          :auto-upload="false"
          :limit="1"
          :on-change="onImportFileChange"
          :on-remove="onImportFileRemove"
        >
          <el-icon style="font-size: 40px; color: #c0c4cc"><upload-filled /></el-icon>
          <div>将 .csv / .txt / .json 文件拖到此处，或点击选择（UTF-8 / GBK 均可）</div>
        </el-upload>
      </el-tab-pane>
    </el-tabs>

    <div class="fmt-help">
      <div class="fmt-title">
        CSV 表头（列顺序无关，缺省列取默认值）：
        <el-button size="small" text type="primary" @click="downloadTemplate">下载 CSV 模板</el-button>
      </div>
      <code class="fmt-cols">标题,题面,难度,时限ms,内存MB,标签,参考答案,示例输入,示例输出,隐藏输入,隐藏输出,公开</code>
      <ul class="fmt-list">
        <li>难度：easy / medium / hard（或 简单 / 中等 / 困难）</li>
        <li>标签用 ; 或 、 分隔；时限默认 2000ms，内存默认 64MB</li>
        <li>示例输入与示例输出按 ||| 切分后一一对应（例：`1 2|||3 4` 表示两组）</li>
        <li>公开：true / false，默认 false</li>
      </ul>
    </div>

    <template v-if="importResult">
      <el-divider />
      <el-alert
        :type="importResult.failed_count ? 'warning' : 'success'"
        :closable="false"
        show-icon
      >
        导入完成：成功 {{ importResult.created_count }} 题，失败 {{ importResult.failed_count }} 行
      </el-alert>
      <el-table v-if="importResult.failed.length" :data="importResult.failed" size="small" max-height="220" class="fail-table">
        <el-table-column prop="row" label="行号" width="70" />
        <el-table-column prop="title" label="标题" min-width="160" />
        <el-table-column prop="error" label="失败原因" min-width="240" />
      </el-table>
    </template>

    <template #footer>
      <el-button @click="importVisible = false">关闭</el-button>
      <el-button type="primary" :loading="importing" @click="doImport">开始导入</el-button>
    </template>
  </el-dialog>

  <!-- 题目编辑对话框 -->
  <el-dialog v-model="dialogVisible" :title="editingId ? '编辑题目' : '新建题目'" width="720px" top="4vh">
    <el-form :model="form" label-width="100px">
      <el-form-item label="标题">
        <el-input v-model="form.title" />
      </el-form-item>
      <el-form-item label="难度">
        <el-select v-model="form.difficulty" style="width: 160px">
          <el-option label="简单" value="easy" />
          <el-option label="中等" value="medium" />
          <el-option label="困难" value="hard" />
        </el-select>
      </el-form-item>
      <el-form-item label="时限/内存">
        <el-input-number v-model="form.time_limit_ms" :min="100" :step="500" controls-position="right" />
        <span class="unit">ms</span>
        <el-input-number v-model="form.memory_limit_kb" :min="1024" :step="4096" controls-position="right" />
        <span class="unit">KB</span>
      </el-form-item>
      <el-form-item label="允许语言">
        <el-select v-model="form.allowed_languages" multiple style="width: 240px">
          <el-option label="Python" value="python" />
        </el-select>
      </el-form-item>
      <el-form-item label="标签">
        <el-select v-model="form.tags" multiple filterable allow-create default-first-option style="width: 100%">
          <el-option v-for="t in allTags" :key="t.id" :label="t.name" :value="t.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="题面 (Markdown)">
        <el-input v-model="form.description" type="textarea" :rows="10" />
      </el-form-item>
      <el-form-item label="参考答案">
        <el-input v-model="form.reference_answer" type="textarea" :rows="4" />
      </el-form-item>
      <el-form-item label="公开">
        <el-switch v-model="form.is_public" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="saving" @click="save">保存</el-button>
    </template>
  </el-dialog>

  <!-- 测试用例抽屉 -->
  <el-drawer v-model="casesVisible" :title="`测试用例 · ${currentProblem?.title || ''}`" size="60%">
    <div class="cases-toolbar">
      <el-button type="primary" size="small" @click="openCaseForm()">新增用例</el-button>
    </div>
    <el-table v-loading="casesLoading" :data="cases" stripe size="small">
      <el-table-column prop="order" label="顺序" width="64" />
      <el-table-column prop="input_data" label="输入" min-width="180" show-overflow-tooltip />
      <el-table-column prop="expected_output" label="期望输出" min-width="180" show-overflow-tooltip />
      <el-table-column label="示例" width="70">
        <template #default="{ row }">
          <el-tag v-if="row.is_sample" size="small" type="success">是</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="隐藏" width="70">
        <template #default="{ row }">
          <el-tag v-if="row.is_hidden" size="small" type="warning">是</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openCaseForm(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="removeCase(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 用例编辑对话框 -->
    <el-dialog v-model="caseDialogVisible" :title="caseForm.id ? '编辑用例' : '新增用例'" width="520px" append-to-body>
      <el-form :model="caseForm" label-width="90px">
        <el-form-item label="顺序">
          <el-input-number v-model="caseForm.order" :min="0" />
        </el-form-item>
        <el-form-item label="输入">
          <el-input v-model="caseForm.input_data" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item label="期望输出">
          <el-input v-model="caseForm.expected_output" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item label="示例用例">
          <el-switch v-model="caseForm.is_sample" />
          <span class="hint">（题面展示给普通用户）</span>
        </el-form-item>
        <el-form-item label="隐藏用例">
          <el-switch v-model="caseForm.is_hidden" />
          <span class="hint">（仅用于判题）</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="caseDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveCase">保存</el-button>
      </template>
    </el-dialog>
  </el-drawer>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import {
  bulkImportProblems,
  createProblem,
  createTestCase,
  deleteProblem,
  deleteTestCase,
  getProblem,
  listAdminProblems,
  listTags,
  listTestCases,
  updateProblem,
  updateTestCase,
} from '@/api/problems'
import { useAuthStore } from '@/stores/auth'
import { difficultyColor, difficultyText } from '@/utils/verdict'

const auth = useAuthStore()

const rows = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const allTags = ref([])
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const editingId = ref(null)

const emptyForm = () => ({
  title: '',
  difficulty: 'easy',
  time_limit_ms: 2000,
  memory_limit_kb: 65536,
  allowed_languages: ['python'],
  tags: [],
  description: '',
  reference_answer: '',
  is_public: false,
})
const form = reactive(emptyForm())

const casesVisible = ref(false)
const casesLoading = ref(false)
const cases = ref([])
const currentProblem = ref(null)
const caseDialogVisible = ref(false)
const caseForm = reactive({ id: null, order: 0, input_data: '', expected_output: '', is_sample: false, is_hidden: true })

async function load() {
  loading.value = true
  try {
    const { data } = await listAdminProblems({ page: page.value, page_size: pageSize.value })
    rows.value = data.results || data
    total.value = data.count ?? rows.value.length
  } catch (e) {
    ElMessage.error(e.message || '加载失败')
  } finally {
    loading.value = false
  }
}

function onPageSizeChange() {
  page.value = 1
  load()
}

function openCreate() {
  editingId.value = null
  Object.assign(form, emptyForm())
  dialogVisible.value = true
}

function openEdit(row) {
  editingId.value = row.id
  Object.assign(form, {
    title: row.title,
    difficulty: row.difficulty,
    time_limit_ms: row.time_limit_ms,
    memory_limit_kb: row.memory_limit_kb,
    allowed_languages: row.allowed_languages || ['python'],
    tags: [], // 编辑时标签需要重新获取详情；简化处理：用列表行的 tag id
    description: '',
    reference_answer: '',
    is_public: row.is_public,
  })
  // 从详情接口拿完整字段（description/reference_answer/tags）
  getProblem(row.id).then(({ data }) => {
    form.description = data.description || ''
    form.reference_answer = data.reference_answer || ''
    form.tags = (data.tags || []).map((t) => t.id)
  })
  dialogVisible.value = true
}

async function save() {
  if (!form.title.trim() || !form.description.trim()) {
    ElMessage.warning('标题和题面不能为空')
    return
  }
  saving.value = true
  try {
    if (editingId.value) {
      await updateProblem(editingId.value, { ...form })
      ElMessage.success('题目已更新')
    } else {
      await createProblem({ ...form })
      ElMessage.success('题目已创建')
      page.value = 1
    }
    dialogVisible.value = false
    load()
  } catch (e) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function remove(row) {
  try {
    await ElMessageBox.confirm(`确定删除题目「${row.title}」？其测试用例与提交记录将一并删除`, '确认', { type: 'warning' })
    await deleteProblem(row.id)
    ElMessage.success('已删除')
    // 删除的是本页最后一条时回退一页，避免停留在空白页
    if (rows.value.length === 1 && page.value > 1) page.value -= 1
    load()
  } catch { /* 取消 */ }
}

// ---- 测试用例 ----
async function openCases(row) {
  currentProblem.value = row
  casesVisible.value = true
  casesLoading.value = true
  try {
    const { data } = await listTestCases(row.id)
    cases.value = data.results || data
  } catch (e) {
    ElMessage.error(e.message || '加载用例失败')
  } finally {
    casesLoading.value = false
  }
}

function openCaseForm(row) {
  Object.assign(caseForm, {
    id: row?.id ?? null,
    order: row?.order ?? cases.value.length,
    input_data: row?.input_data ?? '',
    expected_output: row?.expected_output ?? '',
    is_sample: row?.is_sample ?? false,
    is_hidden: row?.is_hidden ?? true,
  })
  caseDialogVisible.value = true
}

async function saveCase() {
  if (!caseForm.input_data && !caseForm.expected_output && caseForm.input_data !== '') {
    ElMessage.warning('请填写输入与期望输出')
    return
  }
  const payload = {
    order: caseForm.order,
    input_data: caseForm.input_data,
    expected_output: caseForm.expected_output,
    is_sample: caseForm.is_sample,
    is_hidden: caseForm.is_hidden,
  }
  try {
    if (caseForm.id) {
      await updateTestCase(currentProblem.value.id, caseForm.id, payload)
    } else {
      await createTestCase(currentProblem.value.id, payload)
    }
    ElMessage.success('用例已保存')
    caseDialogVisible.value = false
    openCases(currentProblem.value)
  } catch (e) {
    ElMessage.error(e.message || '保存失败')
  }
}

async function removeCase(row) {
  try {
    await ElMessageBox.confirm('确定删除该用例？', '确认', { type: 'warning' })
    await deleteTestCase(currentProblem.value.id, row.id)
    openCases(currentProblem.value)
  } catch { /* 取消 */ }
}

// ---- 批量导入（超管） ----
const importVisible = ref(false)
const importTab = ref('text')
const importText = ref('')
const importFile = ref(null)
const importing = ref(false)
const importResult = ref(null)

const CSV_TEMPLATE = [
  '标题,题面,难度,时限ms,内存MB,标签,参考答案,示例输入,示例输出,隐藏输入,隐藏输出,公开',
  'A+B 问题,"输入一行两个整数 a、b，输出它们的和。",easy,2000,64,入门;模拟,,"1 2","3","10 20|||100 200","30|||300",true',
  '字符串反转,"输入一行字符串，输出其反转结果。",medium,2000,64,字符串,,hello,olleh,world,dlrow,false',
].join('\n')

function onImportFileChange(uploadFile) {
  importFile.value = uploadFile.raw || null
}

function onImportFileRemove() {
  importFile.value = null
}

function downloadTemplate() {
  // 加 BOM 保证 Excel 打开不乱码
  const blob = new Blob(['\ufeff' + CSV_TEMPLATE], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = '题目批量导入模板.csv'
  a.click()
  URL.revokeObjectURL(url)
}

async function doImport() {
  if (importTab.value === 'file') {
    if (!importFile.value) {
      ElMessage.warning('请先选择 .csv / .txt / .json 文件')
      return
    }
  } else if (!importText.value.trim()) {
    ElMessage.warning('请粘贴 CSV 或 JSON 内容')
    return
  }
  importing.value = true
  importResult.value = null
  try {
    const payload =
      importTab.value === 'file' && importFile.value
        ? (() => {
            const fd = new FormData()
            fd.append('file', importFile.value)
            return fd
          })()
        : { content: importText.value }
    const { data } = await bulkImportProblems(payload)
    importResult.value = data
    ElMessage.success(`导入完成：成功 ${data.created_count} 题，失败 ${data.failed_count} 行`)
    page.value = 1
    load()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || e.message || '导入失败')
  } finally {
    importing.value = false
  }
}

onMounted(async () => {
  load()
  try {
    const { data } = await listTags()
    allTags.value = data
  } catch { /* ignore */ }
})
</script>

<style scoped>
.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
.pager {
  margin-top: 16px;
  justify-content: flex-end;
}
.unit {
  margin: 0 12px 0 6px;
  color: #909399;
}
.cases-toolbar {
  margin-bottom: 12px;
}
.hint {
  color: #c0c4cc;
  font-size: 12px;
  margin-left: 8px;
}
.import-alert {
  margin-bottom: 12px;
}
.fmt-help {
  margin-top: 12px;
  padding: 10px 12px;
  background: #f5f7fa;
  border-radius: 6px;
}
.fmt-title {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 6px;
}
.fmt-cols {
  display: block;
  font-size: 12px;
  color: #606266;
  word-break: break-all;
  margin-bottom: 6px;
}
.fmt-list {
  margin: 0;
  padding-left: 18px;
  font-size: 12px;
  color: #909399;
  line-height: 1.9;
}
.fail-table {
  margin-top: 10px;
}
</style>
