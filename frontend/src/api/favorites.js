import request from './request'

export const listFavorites = (params) => request.get('/favorites/', { params })
export const toggleFavorite = (problemId) =>
  request.post('/favorites/toggle/', { problem_id: problemId })
export const removeFavorite = (id) => request.delete(`/favorites/${id}/`)
