import { defineStore } from 'pinia'

export const useAssistantStore = defineStore('assistant', {
  state: () => ({
    open: false,
    // 当前题目上下文（进入题目详情页时设置）
    problemContext: null, // { id, title }
  }),
  actions: {
    toggle(open) {
      this.open = open ?? !this.open
    },
    setProblem(problem) {
      this.problemContext = problem ? { id: problem.id, title: problem.title } : null
    },
    clearProblem() {
      this.problemContext = null
    },
  },
})
