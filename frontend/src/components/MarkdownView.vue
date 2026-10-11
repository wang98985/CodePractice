<template>
  <div class="markdown-view" v-html="html"></div>
</template>

<script setup>
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'
import DOMPurify from 'dompurify'

const props = defineProps({ content: { type: String, default: '' } })

const md = new MarkdownIt({ html: false, linkify: true, breaks: false })

const html = computed(() => DOMPurify.sanitize(md.render(props.content || '')))
</script>

<style scoped>
.markdown-view {
  line-height: 1.8;
  word-break: break-word;
}
.markdown-view :deep(pre) {
  background: #282c34;
  color: #abb2bf;
  padding: 12px 16px;
  border-radius: 6px;
  overflow-x: auto;
}
.markdown-view :deep(code) {
  background: #f0f2f5;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}
.markdown-view :deep(pre code) {
  background: transparent;
  padding: 0;
}
.markdown-view :deep(table) {
  border-collapse: collapse;
  margin: 8px 0;
}
.markdown-view :deep(th),
.markdown-view :deep(td) {
  border: 1px solid #dcdfe6;
  padding: 6px 12px;
}
.markdown-view :deep(blockquote) {
  border-left: 4px solid #409eff;
  margin: 8px 0;
  padding: 4px 12px;
  color: #606266;
  background: #ecf5ff;
}
</style>
