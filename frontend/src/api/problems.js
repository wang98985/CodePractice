import request from './request'

export const listProblems = (params) => request.get('/problems/', { params })
export const getProblem = (id) => request.get(`/problems/${id}/`)
export const listTags = () => request.get('/tags/')

// ---- 管理端 ----
export const listAdminProblems = (params) => request.get('/admin/problems/', { params })
export const createProblem = (data) => request.post('/problems/', data)
export const updateProblem = (id, data) => request.patch(`/problems/${id}/`, data)
export const deleteProblem = (id) => request.delete(`/problems/${id}/`)
// 批量导入：JSON body {content} 或 FormData（含 file 字段）
export const bulkImportProblems = (payload) => request.post('/problems/admin/bulk-upload/', payload)

export const listTestCases = (problemId) => request.get(`/problems/${problemId}/test-cases/`)
export const createTestCase = (problemId, data) =>
  request.post(`/problems/${problemId}/test-cases/`, data)
export const updateTestCase = (problemId, id, data) =>
  request.patch(`/problems/${problemId}/test-cases/${id}/`, data)
export const deleteTestCase = (problemId, id) =>
  request.delete(`/problems/${problemId}/test-cases/${id}/`)
