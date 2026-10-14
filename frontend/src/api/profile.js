import request from './request'

export const fetchProfile = (id) => request.get(`/users/${id}/profile/`)
