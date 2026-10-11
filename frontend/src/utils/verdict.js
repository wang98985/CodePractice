export const VERDICT_MAP = {
  pending: { text: '等待判题', type: 'info' },
  judging: { text: '判题中', type: 'warning' },
  accepted: { text: '通过', type: 'success' },
  wrong_answer: { text: '答案错误', type: 'danger' },
  time_limit_exceeded: { text: '超时', type: 'danger' },
  memory_limit_exceeded: { text: '内存超限', type: 'danger' },
  runtime_error: { text: '运行时错误', type: 'danger' },
  compile_error: { text: '编译错误', type: 'warning' },
  system_error: { text: '系统错误', type: 'info' },
}

export const NON_TERMINAL = new Set(['pending', 'judging'])

export function verdictText(status) {
  return VERDICT_MAP[status]?.text ?? status
}

export function verdictType(status) {
  return VERDICT_MAP[status]?.type ?? 'info'
}

export const DIFFICULTY_MAP = {
  easy: { text: '简单', color: '#67c23a' },
  medium: { text: '中等', color: '#e6a23c' },
  hard: { text: '困难', color: '#f56c6c' },
}

export function difficultyText(d) {
  return DIFFICULTY_MAP[d]?.text ?? d
}

export function difficultyColor(d) {
  return DIFFICULTY_MAP[d]?.color ?? '#909399'
}
