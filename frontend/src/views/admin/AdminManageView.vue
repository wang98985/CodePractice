<template>
  <el-card>
    <div class="toolbar">
      <el-button type="primary" @click="openCreate">创建管理员</el-button>
    </div>

    <el-table v-loading="loading" :data="rows" stripe>
      <el-table-column prop="id" label="ID" width="72" />
      <el-table-column prop="username" label="用户名" min-width="140" />
      <el-table-column prop="email" label="邮箱" min-width="200" />
      <el-table-column label="角色" width="130">
        <template #default="{ row }">
          <el-tag size="small" :type="row.role === 'super_admin' ? 'danger' : 'warning'">
            {{ roleText(row.role) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
            {{ row.is_active ? '正常' : '已禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="date_joined" label="创建时间" width="180">
        <template #default="{ row }">{{ formatTime(row.date_joined) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="row.role === 'admin'"
            size="small"
            type="warning"
            @click="demote(row)"
          >
            降为普通用户
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>

  <!-- 创建管理员对话框 -->
  <el-dialog v-model="dialogVisible" title="创建管理员" width="420px">
    <el-form :model="form" label-width="80px">
      <el-form-item label="用户名">
        <el-input v-model="form.username" />
      </el-form-item>
      <el-form-item label="邮箱">
        <el-input v-model="form.email" />
      </el-form-item>
      <el-form-item label="初始密码">
        <el-input v-model="form.password" show-password />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="creating" @click="create">创建</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createAdmin, listAdmins, setUserRole } from '@/api/admin'

const rows = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const creating = ref(false)
const form = reactive({ username: '', email: '', password: '' })

const roleText = (r) => ({ admin: '管理员', super_admin: '超级管理员' }[r] || r)
const formatTime = (t) => (t ? new Date(t).toLocaleString('zh-CN', { hour12: false }) : '-')

async function load() {
  loading.value = true
  try {
    const { data } = await listAdmins()
    rows.value = data.results || data
  } catch (e) {
    ElMessage.error(e.message || '加载失败')
  } finally {
    loading.value = false
  }
}

function openCreate() {
  form.username = ''
  form.email = ''
  form.password = ''
  dialogVisible.value = true
}

async function create() {
  if (!form.username || !form.email || !form.password) {
    ElMessage.warning('请填写完整信息')
    return
  }
  creating.value = true
  try {
    await createAdmin({ ...form })
    ElMessage.success('管理员创建成功')
    dialogVisible.value = false
    load()
  } catch (e) {
    ElMessage.error(e.message || '创建失败')
  } finally {
    creating.value = false
  }
}

async function demote(row) {
  try {
    await ElMessageBox.confirm(`确定将管理员 ${row.username} 降为普通用户？`, '确认', { type: 'warning' })
    await setUserRole(row.id, 'user')
    ElMessage.success('已降级')
    load()
  } catch { /* 取消 */ }
}

onMounted(load)
</script>

<style scoped>
.toolbar {
  margin-bottom: 16px;
}
</style>
