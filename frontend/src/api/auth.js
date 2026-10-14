import request from './request'

export const login = (data) => request.post('/auth/login/', data)
export const register = (data) => request.post('/auth/register/', data)
export const sendEmailCode = (email, purpose = 'register') =>
  request.post('/auth/send-email-code/', { email, purpose })
export const resetPassword = (data) => request.post('/auth/reset-password/', data)
export const refreshApi = (refresh) => request.post('/auth/refresh/', { refresh })
export const fetchMe = () => request.get('/auth/me/')
export const updateMe = (data) => request.patch('/auth/me/', data)
