<template>
  <span class="user-avatar" :style="avatarStyle">{{ initial }}</span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  name: { type: String, default: '' },
  size: { type: [Number, String], default: 40 },
})

// 8 组渐变，按用户名哈希确定，同一用户颜色稳定
const PALETTE = [
  'linear-gradient(135deg,#6366f1,#4f46e5)',
  'linear-gradient(135deg,#0ea5e9,#2563eb)',
  'linear-gradient(135deg,#10b981,#059669)',
  'linear-gradient(135deg,#f59e0b,#d97706)',
  'linear-gradient(135deg,#ef4444,#dc2626)',
  'linear-gradient(135deg,#8b5cf6,#6d28d9)',
  'linear-gradient(135deg,#ec4899,#db2777)',
  'linear-gradient(135deg,#14b8a6,#0d9488)',
]

const initial = computed(() => {
  const s = (props.name || '').trim()
  return s ? s[0].toUpperCase() : '?'
})

const gradient = computed(() => {
  const s = props.name || ''
  let hash = 0
  for (let i = 0; i < s.length; i += 1) {
    hash = (hash * 31 + s.charCodeAt(i)) >>> 0
  }
  return PALETTE[hash % PALETTE.length]
})

const avatarStyle = computed(() => {
  const px = Number(props.size) || 40
  return {
    width: `${px}px`,
    height: `${px}px`,
    fontSize: `${Math.round(px * 0.42)}px`,
    background: gradient.value,
  }
})
</script>

<style scoped>
.user-avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  color: #fff;
  font-weight: 600;
  user-select: none;
  flex-shrink: 0;
  box-shadow: var(--shadow-1);
}
</style>
