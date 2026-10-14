<template>
  <div class="stat-card" :style="{ '--accent': color }">
    <div class="stat-card__icon">
      <el-icon :size="22"><component :is="icon" /></el-icon>
    </div>
    <div class="stat-card__body">
      <div class="stat-card__value">{{ value }}</div>
      <div class="stat-card__label">{{ label }}</div>
      <div v-if="hint" class="stat-card__hint">{{ hint }}</div>
    </div>
  </div>
</template>

<script setup>
import { DataLine } from '@element-plus/icons-vue'

defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], default: '-' },
  icon: { type: [Object, Function], default: () => DataLine },
  color: { type: String, default: '#4f46e5' },
  hint: { type: String, default: '' },
})
</script>

<style scoped>
.stat-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 20px;
  background: #fff;
  border: 1px solid var(--c-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-1);
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}
.stat-card:hover {
  box-shadow: var(--shadow-2);
  transform: translateY(-2px);
}
.stat-card__icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent);
  background: color-mix(in srgb, var(--accent) 14%, #fff);
  flex-shrink: 0;
}
.stat-card__value {
  font-size: 24px;
  font-weight: 700;
  line-height: 1.2;
  color: var(--c-text);
}
.stat-card__label {
  font-size: 13px;
  color: var(--c-text-secondary);
  margin-top: 2px;
}
.stat-card__hint {
  font-size: 12px;
  color: var(--c-text-secondary);
  margin-top: 4px;
}
</style>
