import axios from 'axios'
import router from '@/router'
import { useAuthStore } from '@/stores/auth'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
})

request.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.accessToken) {
    config.headers.Authorization = `Bearer ${auth.accessToken}`
  }
  return config
})

let refreshing = null

request.interceptors.response.use(
  (resp) => resp,
  async (error) => {
    const auth = useAuthStore()
    const { response, config } = error

    // 401 时用 refresh token 换新并重放原请求
    if (response?.status === 401 && auth.refreshToken && config && !config._retried) {
      config._retried = true
      try {
        refreshing = refreshing || auth.refresh().finally(() => { refreshing = null })
        await refreshing
        config.headers.Authorization = `Bearer ${auth.accessToken}`
        return request(config)
      } catch (e) {
        auth.logout()
        router.push('/login')
        return Promise.reject(error)
      }
    }

    const data = response?.data
    const msg = data?.detail
      || (data && typeof data === 'object' ? Object.values(data).flat().join('；') : null)
      || error.message
    return Promise.reject({ ...error, message: msg })
  }
)

export default request
