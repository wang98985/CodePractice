import request from './request'

// 每日一题：今日题目 + 最近 6 天历史（含我的通过状态）
export const getDailyProblem = () => request.get('/daily/')
