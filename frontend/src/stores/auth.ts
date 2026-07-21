import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api, { guestSession, getPageVisibility } from '../api'

interface User {
  id: number
  username: string
  email: string
  display_name: string
  role: string
  avatar_url: string
  is_active: boolean
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('wp_token'))
  const isAuthenticated = computed(() => !!token.value)
  const visiblePages = ref<string[]>([])
  const pageVisibilityLoaded = ref(false)

  function setAuth(t: string, u: User) {
    token.value = t
    user.value = u
    localStorage.setItem('wp_token', t)
    api.defaults.headers.common['Authorization'] = `Bearer ${t}`
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('wp_token')
    delete api.defaults.headers.common['Authorization']
  }

  async function fetchMe() {
    if (!token.value) return
    api.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
    try {
      const { data } = await api.get('/auth/me')
      user.value = data
    } catch {
      logout()
    }
  }

  function isAdmin() {
    return user.value?.role === 'admin'
  }

  async function loginAsGuest() {
    try {
      const { data } = await guestSession()
      setAuth(data.access_token, data.user)
      await loadPageVisibility()
      return true
    } catch {
      return false
    }
  }

  async function loadPageVisibility() {
    if (!token.value) return
    try {
      const { data } = await getPageVisibility()
      visiblePages.value = data.pages || []
      pageVisibilityLoaded.value = true
    } catch {
      visiblePages.value = []
    }
  }

  function canAccessPage(path: string): boolean {
    if (user.value?.role === 'admin') return true
    if (!pageVisibilityLoaded.value) return true // not yet loaded, allow
    if (!visiblePages.value.length) return true // empty = no restriction
    return visiblePages.value.includes(path)
  }

  return { user, token, isAuthenticated, visiblePages, pageVisibilityLoaded, setAuth, logout, fetchMe, isAdmin, loginAsGuest, loadPageVisibility, canAccessPage }
})
