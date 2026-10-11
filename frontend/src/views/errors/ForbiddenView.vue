<template>
  <el-result icon="warning" title="403" sub-title="没有权限访问该页面">
    <template #extra>
      <el-button type="primary" @click="$router.push('/problems')">返回题库</el-button>
    </template>
  </el-result>
</template>
