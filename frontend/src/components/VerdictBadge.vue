<template>
  <el-tag :type="verdictType(status)" effect="dark" size="small">
    {{ verdictText(status) }}
  </el-tag>
</template>

<script setup>
import { verdictText, verdictType } from '@/utils/verdict'

defineProps({ status: { type: String, required: true } })
</script>
