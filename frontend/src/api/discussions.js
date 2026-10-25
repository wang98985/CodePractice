import request from './request'

export const listDiscussions = (problemId, params) =>
  request.get(`/problems/${problemId}/discussions/`, { params })
export const createDiscussion = (problemId, data) =>
  request.post(`/problems/${problemId}/discussions/`, data)
export const getDiscussion = (id) => request.get(`/discussions/${id}/`)
export const deleteDiscussion = (id) => request.delete(`/discussions/${id}/`)
export const createReply = (id, content) =>
  request.post(`/discussions/${id}/replies/`, { content })
export const deleteReply = (id) => request.delete(`/discussion-replies/${id}/`)
