import { defineStore } from 'pinia'
import { ref } from 'vue'

interface Tab { id: number; title: string; path: string }

export const useTabStore = defineStore('tabs', () => {
  const tabs = ref<Tab[]>([])
  const activeTabId = ref<number | null>(null)
  let nextId = 1

  function openTab(title: string, path: string) {
    const existing = tabs.value.find(t => t.path === path)
    if (existing) { activeTabId.value = existing.id; return }
    const tab: Tab = { id: nextId++, title, path }
    tabs.value.push(tab)
    activeTabId.value = tab.id
  }

  function closeTab(id: number) {
    const idx = tabs.value.findIndex(t => t.id === id)
    if (idx === -1) return
    tabs.value.splice(idx, 1)
    if (activeTabId.value === id) {
      activeTabId.value = tabs.value.length > 0 ? tabs.value[Math.min(idx, tabs.value.length - 1)].id : null
    }
  }

  function switchTab(id: number) {
    activeTabId.value = id
    const tab = tabs.value.find(t => t.id === id)
    if (tab) window.location.hash = tab.path
  }

  return { tabs, activeTabId, openTab, closeTab, switchTab }
})
