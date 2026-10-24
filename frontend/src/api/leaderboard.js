import request from './request'

export const getLeaderboard = (params) => request.get('/leaderboard/', { params })
