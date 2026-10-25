import request from './request'

export const listProblemSets = () => request.get('/problem-sets/')
export const getProblemSet = (id) => request.get(`/problem-sets/${id}/`)
export const createProblemSet = (data) => request.post('/problem-sets/', data)
export const updateProblemSet = (id, data) => request.patch(`/problem-sets/${id}/`, data)
export const deleteProblemSet = (id) => request.delete(`/problem-sets/${id}/`)
export const addProblemToSet = (id, problemId) =>
  request.post(`/problem-sets/${id}/items/`, { problem_id: problemId })
export const removeProblemFromSet = (id, itemId) =>
  request.delete(`/problem-sets/${id}/items/${itemId}/`)
