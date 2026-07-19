import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { getSetting, updateSetting } from '../api'

export type LayoutMode = 'card' | 'list' | 'desktop' | 'sidebar'
export type ThemeMode = 'light' | 'dark' | 'auto'

export const useSettingsStore = defineStore('settings', () => {
  const layoutMode = ref<LayoutMode>('card')
  const themeMode = ref<ThemeMode>('auto')
  const sidebarCollapsed = ref(false)
  const globalSearchOpen = ref(false)

  const isDark = ref(false)

  function applyTheme(mode: ThemeMode) {
    const root = document.documentElement
    if (mode === 'dark') {
      root.classList.add('dark')
      isDark.value = true
    } else if (mode === 'light') {
      root.classList.remove('dark')
      isDark.value = false
    } else {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      if (prefersDark) {
        root.classList.add('dark')
        isDark.value = true
      } else {
        root.classList.remove('dark')
        isDark.value = false
      }
    }
  }

  async function loadSettings() {
    try {
      const layoutResp = await getSetting('layout_mode')
      if (layoutResp.data.value) layoutMode.value = layoutResp.data.value as LayoutMode
      const themeResp = await getSetting('theme_mode')
      if (themeResp.data.value) themeMode.value = themeResp.data.value as ThemeMode
    } catch { /* use defaults */ }
    applyTheme(themeMode.value)
  }

  async function setLayoutMode(mode: LayoutMode) {
    layoutMode.value = mode
    await updateSetting('layout_mode', mode)
  }

  async function setThemeMode(mode: ThemeMode) {
    themeMode.value = mode
    applyTheme(mode)
    await updateSetting('theme_mode', mode)
  }

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function toggleSearch() {
    globalSearchOpen.value = !globalSearchOpen.value
  }

  watch(() => themeMode.value, applyTheme)

  // Listen for system theme changes in auto mode
  if (typeof window !== 'undefined') {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
      if (themeMode.value === 'auto') applyTheme('auto')
    })
  }

  return {
    layoutMode, themeMode, sidebarCollapsed, globalSearchOpen, isDark,
    loadSettings, setLayoutMode, setThemeMode, toggleSidebar, toggleSearch
  }
})
