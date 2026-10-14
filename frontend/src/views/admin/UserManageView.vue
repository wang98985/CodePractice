<template>
  <div>
    <PageHeader title="用户管理" subtitle="查看与管理平台普通用户（启用 / 禁用、重置密码、调整角色）" />

    <div class="toolbar">
      <el-input
        v-model="search"
        placeholder="搜索昵称/邮箱"
        clearable
        style="width: 220px"
        @keyup.enter="load(1)"
        @clear="load(1)"
      />
      <el-button type="primary" @click="load(1)">搜索</el-button>
    </div>

    <el-card shadow="never">
    <el-table v-loading="loading" :data="rows" stripe>
      <el-table-column prop="id" label="ID" width="72" />
      <el-table-column prop="nickname" label="昵称" min-width="140" />
      <el-table-column prop="email" label="邮箱" min-width="200" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
            {{ row.is_active ? '正常' : '已禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="角色" width="110">
        <template #default="{ row }">
          <el-tag size="small" type="info">{{ roleText(row.role) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="date_joined" label="注册时间" width="180">
        <template #default="{ row }">{{ formatTime(row.date_joined) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="240" fixed="right">
        <template #default="{ row }">
          <el-switch
            :model-value="row.is_active"
            inline-prompt
            active-text="启用"
            inactive-text="禁用"
            style="margin-right: 8px"
            @change="(val) => toggleActive(row, val)"
          />
          <el-button size="small" @click="resetPassword(row)">重置密码</el-button>
          <el-button
            v-if="auth.isSuperAdmin"
            size="small"
            type="warning"
            @click="changeRole(row)"
          >
            改角色
          </el-button>
        </template>
      </el-table-column>
    </el-table>

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
import { ElMessage, ElMessageBox } from 'element-plus'
import { listUsers, patchUser, setUserRole } from '@/api/admin'
import { useAuthStore } from '@/stores/auth'
import PageHeader from '@/components/PageHeader.vue'

const auth = useAuthStore()
const rows = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const search = ref('')

const roleText = (r) => ({ user: '普通用户', admin: '管理员', super_admin: '超级管理员' }[r] || r)
const formatTime = (t) => (t ? new Date(t).toLocaleString('zh-CN', { hour12: false }) : '-')

async function load(p = page.value) {
  page.value = p
  loading.value = true
  try {
    const params = { page: p }
    if (search.value) params.search = search.value
    const { data } = await listUsers(params)
    rows.value = data.results
    total.value = data.count
  } catch (e) {
    ElMessage.error(e.message || '加载失败')
  } finally {
    loading.value = false
  }
}

async function toggleActive(row, val) {
  try {
    await patchUser(row.id, { is_active: val })
    row.is_active = val
    ElMessage.success(val ? '已启用' : '已禁用')
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  }
}

async function resetPassword(row) {
  try {
    const { value } = await ElMessageBox.prompt(`为用户 ${row.nickname || row.email} 设置新密码（至少 6 位）`, '重置密码', {
      inputType: 'password',
      inputPattern: /^.{6,}$/,
      inputErrorMessage: '密码至少 6 位',
    })
    await patchUser(row.id, { password: value })
    ElMessage.success('密码已重置')
  } catch { /* 取消 */ }
}

async function changeRole(row) {
  try {
    const { value } = await ElMessageBox.prompt(
      `将 ${row.nickname || row.email} 的角色设置为（user / admin / super_admin）`,
      '修改角色',
      { inputValue: row.role }
    )
    await setUserRole(row.id, value.trim())
    ElMessage.success('角色已更新')
    load(page.value)
  } catch (e) {
    if (e?.message) ElMessage.error(e.message)
  }
}

onMounted(() => load(1))
</script>
