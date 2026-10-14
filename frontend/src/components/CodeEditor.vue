<template>
  <div ref="container" class="code-editor"></div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { basicSetup, EditorView } from 'codemirror'
import { Compartment } from '@codemirror/state'
import { python } from '@codemirror/lang-python'
import { cpp } from '@codemirror/lang-cpp'
import { java } from '@codemirror/lang-java'
import { oneDark } from '@codemirror/theme-one-dark'

const props = defineProps({
  modelValue: { type: String, default: '' },
  language: { type: String, default: 'python' },
})
const emit = defineEmits(['update:modelValue'])

const container = ref(null)
let view = null
const langCompartment = new Compartment()

const langExts = {
  python: python(),
  cpp: cpp(),
  java: java(),
}

onMounted(() => {
  view = new EditorView({
    doc: props.modelValue || '',
    extensions: [
      basicSetup,
      langCompartment.of(langExts[props.language] || python()),
      oneDark,
      EditorView.updateListener.of((update) => {
        if (update.docChanged) {
          emit('update:modelValue', update.state.doc.toString())
        }
      }),
    ],
    parent: container.value,
  })
})

watch(
  () => props.language,
  (lang) => {
    view?.dispatch({ effects: langCompartment.reconfigure(langExts[lang] || python()) })
  }
)

watch(
  () => props.modelValue,
  (val) => {
    if (view && val != null && view.state.doc.toString() !== val) {
      view.dispatch({ changes: { from: 0, to: view.state.doc.length, insert: val } })
    }
  }
)

onBeforeUnmount(() => view?.destroy())

defineExpose({
  getValue: () => view?.state.doc.toString() ?? '',
})
</script>

<style scoped>
.code-editor {
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  overflow: hidden;
}
.code-editor :deep(.cm-editor) {
  min-height: 320px;
  max-height: 480px;
  font-size: 14px;
}
.code-editor :deep(.cm-scroller) {
  overflow-y: auto;
}
/* 手机端：压低编辑器高度，避免一屏放不下提交按钮 */
@media (max-width: 560px) {
  .code-editor :deep(.cm-editor) {
    min-height: 240px;
    max-height: 46vh;
    font-size: 13px;
  }
}
</style>
