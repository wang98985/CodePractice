import request from './request'

export const listUsers = (params) => request.get('/admin/users/', { params })
export const patchUser = (id, data) => request.patch(`/admin/users/${id}/`, data)
export const setUserRole = (id, role) =>
  request.patch(`/admin/users/${id}/set-role/`, { role })
export const listAdmins = () => request.get('/admin/admins/')
export const createAdmin = (data) => request.post('/admin/admins/', data)
export const fetchDashboard = () => request.get('/admin/dashboard/')
