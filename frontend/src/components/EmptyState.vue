<template>
  <div class="empty-state">
    <el-icon class="empty-state__icon" :size="iconSize"><component :is="icon" /></el-icon>
    <p class="empty-state__text">{{ description }}</p>
    <div v-if="$slots.default" class="empty-state__actions">
      <slot />
    </div>
  </div>
</template>

<script setup>
import { Document } from '@element-plus/icons-vue'

defineProps({
  description: { type: String, default: '暂无数据' },
  icon: { type: [Object, Function], default: () => Document },
  iconSize: { type: Number, default: 52 },
})
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
}
.empty-state__icon {
  color: #c8cddb;
}
.empty-state__text {
  margin: 14px 0 0;
  color: var(--c-text-secondary);
  font-size: 14px;
}
.empty-state__actions {
  margin-top: 16px;
}
</style>
