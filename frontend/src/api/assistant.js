import request from './request'

// SSE 流式聊天（axios 不支持流式读取，使用 fetch + ReadableStream）
export async function streamChat(payload, handlers = {}, signal = undefined) {
  const token = localStorage.getItem('access')
  const base = import.meta.env.VITE_API_BASE_URL || '/api'
  const resp = await fetch(`${base}/assistant/chat/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: token ? `Bearer ${token}` : '',
    },
    body: JSON.stringify(payload),
    signal,
  })

  if (!resp.ok || !resp.body) {
    let msg = `HTTP ${resp.status}`
    try {
      const data = await resp.json()
      msg = data.detail || (data && typeof data === 'object' ? Object.values(data).flat().join('；') : msg) || msg
    } catch { /* ignore */ }
    throw new Error(msg)
  }

  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    let idx
    while ((idx = buffer.indexOf('\n\n')) !== -1) {
      const rawEvent = buffer.slice(0, idx)
      buffer = buffer.slice(idx + 2)
      for (const line of rawEvent.split('\n')) {
        if (!line.startsWith('data:')) continue
        let data
        try {
          data = JSON.parse(line.slice(5).trim())
        } catch { continue }
        if (data.delta) handlers.onDelta?.(data.delta)
        else if (data.event === 'notice') handlers.onNotice?.(data.message)
        else if (data.event === 'error') handlers.onError?.(data.message)
        else if (data.event === 'done') handlers.onDone?.()
      }
    }
  }
}

export const listSessions = (params) => request.get('/assistant/sessions/', { params })
export const createSession = (data) => request.post('/assistant/sessions/', data)
export const deleteSession = (id) => request.delete(`/assistant/sessions/${id}/`)
export const fetchSessionMessages = (id) =>
  request.get(`/assistant/sessions/${id}/messages/`)
