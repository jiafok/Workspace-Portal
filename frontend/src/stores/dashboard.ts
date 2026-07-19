import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getDashboard } from '../api'

export const useDashboardStore = defineStore('dashboard', () => {
  const systemInfo = ref({
    cpu_percent: 0,
    memory_percent: 0,
    memory_used_gb: 0,
    memory_total_gb: 0,
    disk_percent: 0,
    disk_used_gb: 0,
    disk_total_gb: 0,
    hostname: '',
    os: '',
  })
  const recentWebsites = ref<any[]>([])
  const recentAI = ref<any[]>([])
  const stats = ref({ total_websites: 0, total_categories: 0, total_ai: 0, total_nas: 0 })
  const currentTime = ref('')
  const weather = ref({ temp: '--', desc: '加载中...', city: '' })
  let timer: number | null = null

  function updateTime() {
    const now = new Date()
    currentTime.value = now.toLocaleString('zh-CN', {
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
      weekday: 'long',
    })
  }

  async function fetchDashboard() {
    try {
      const { data } = await getDashboard()
      systemInfo.value = data.system
      recentWebsites.value = data.recent_websites
      recentAI.value = data.recent_ai
      stats.value = data.stats
    } catch { /* ignore */ }
  }

  function startTimers() {
    updateTime()
    timer = window.setInterval(updateTime, 1000)
  }

  function stopTimers() {
    if (timer !== null) {
      clearInterval(timer)
      timer = null
    }
  }

  return {
    systemInfo, recentWebsites, recentAI, stats, currentTime, weather,
    fetchDashboard, startTimers, stopTimers, updateTime
  }
})
