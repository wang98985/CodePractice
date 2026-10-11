import request from './request'

export const createSubmission = (data) => request.post('/submissions/', data)
export const listSubmissions = (params) => request.get('/submissions/', { params })
export const getSubmission = (id) => request.get(`/submissions/${id}/`)
export const getSubmissionStatus = (id) => request.get(`/submissions/${id}/status/`)
