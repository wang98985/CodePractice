import request from './request'

export const listAchievements = () => request.get('/achievements/')
