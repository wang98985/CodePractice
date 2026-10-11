import request from './request'

export const login = (data) => request.post('/auth/login/', data)
export const register = (data) => request.post('/auth/register/', data)
export const sendEmailCode = (email) => request.post('/auth/send-email-code/', { email })
export const refreshApi = (refresh) => request.post('/auth/refresh/', { refresh })
export const fetchMe = () => request.get('/auth/me/')
export const updateMe = (data) => request.put('/auth/me/', data)
