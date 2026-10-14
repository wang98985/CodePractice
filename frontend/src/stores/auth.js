import { defineStore } from 'pinia'
import { fetchMe, login as apiLogin, refreshApi, register as apiRegister } from '@/api/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    accessToken: localStorage.getItem('access') || '',
    refreshToken: localStorage.getItem('refresh') || '',
    user: JSON.parse(localStorage.getItem('user') || 'null'),
  }),
  getters: {
    isLoggedIn: (s) => !!s.accessToken,
    role: (s) => s.user?.role || 'user',
    isAdmin: (s) => s.user?.role === 'admin' || s.user?.role === 'super_admin',
    isSuperAdmin: (s) => s.user?.role === 'super_admin',
  },
  actions: {
    async login(email, password) {
      const { data } = await apiLogin({ email, password })
      this.accessToken = data.access
      this.refreshToken = data.refresh
      this.user = data.user
      this._persist()
    },
    async register(payload) {
      await apiRegister(payload)
    },
    async refresh() {
      const { data } = await refreshApi(this.refreshToken)
      this.accessToken = data.access
      if (data.refresh) this.refreshToken = data.refresh
      this._persist()
      return data.access
    },
    async fetchMe() {
      const { data } = await fetchMe()
      this.user = data
      this._persist()
    },
    logout() {
      this.accessToken = ''
      this.refreshToken = ''
      this.user = null
      localStorage.removeItem('access')
      localStorage.removeItem('refresh')
      localStorage.removeItem('user')
    },
    _persist() {
      localStorage.setItem('access', this.accessToken)
      localStorage.setItem('refresh', this.refreshToken)
      if (this.user) localStorage.setItem('user', JSON.stringify(this.user))
      else localStorage.removeItem('user')
    },
  },
})
