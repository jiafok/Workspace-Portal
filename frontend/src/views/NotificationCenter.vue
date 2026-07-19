<template>
  <div class="notif-center">
    <div class="page-header">
      <h2><el-icon><Bell /></el-icon> 通知中心</h2>
      <el-button @click="markAll" :disabled="!unreadCount">全部已读</el-button>
    </div>

    <div v-if="notifications.length" class="notif-list">
      <div v-for="n in notifications" :key="n.id" :class="['notif-item', 'glass', { unread: !n.is_read }]" @click="openNotif(n)">
        <div class="notif-icon" :class="n.level">
          <el-icon size="16"><component :is="levelIcon(n.level)" /></el-icon>
        </div>
        <div class="notif-main">
          <span class="notif-title">{{ n.title }}</span>
          <span v-if="n.body" class="notif-body">{{ n.body }}</span>
          <span class="notif-meta">{{ n.source }} · {{ formatDate(n.created_at) }}</span>
        </div>
        <div v-if="!n.is_read" class="unread-dot"></div>
      </div>
    </div>
    <el-empty v-else description="暂无通知" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '../api'

const notifications = ref<any[]>([])
const unreadCount = computed(() => notifications.value.filter(n => !n.is_read).length)

function levelIcon(l: string) {
  const m: Record<string, string> = { info: 'InfoFilled', warning: 'WarningFilled', error: 'CircleCloseFilled', success: 'CircleCheckFilled' }
  return m[l] || 'InfoFilled'
}
function formatDate(d: string) { return new Date(d).toLocaleString('zh-CN') }

async function openNotif(n: any) {
  if (!n.is_read) { await api.put(`/monitoring/notifications/${n.id}/read`); n.is_read = true }
  if (n.link) window.open(n.link, '_blank')
}
async function markAll() { await api.put('/monitoring/notifications/read-all'); notifications.value.forEach(n => n.is_read = true) }
async function fetchNotifs() {
  try { const { data } = await api.get('/monitoring/notifications', { params: { limit: 100 } }); notifications.value = data } catch { /* */ }
}

onMounted(fetchNotifs)
</script>

<style scoped>
.notif-center { max-width: 800px; margin: 0 auto; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.page-header h2 { display: flex; align-items: center; gap: 8px; font-size: 22px; font-weight: 800; }
.notif-list { display: flex; flex-direction: column; gap: 6px; }
.notif-item { display: flex; align-items: flex-start; gap: 12px; padding: 14px 16px; cursor: pointer; }
.notif-item.unread { border-left: 3px solid var(--accent); }
.notif-icon { width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.notif-icon.info { background: #0984e322; color: #0984e3; }
.notif-icon.warning { background: #fdcb6e22; color: #fdcb6e; }
.notif-icon.error { background: #e1705522; color: #e17055; }
.notif-icon.success { background: #00b89422; color: #00b894; }
.notif-main { flex: 1; }
.notif-title { font-size: 14px; font-weight: 600; display: block; }
.notif-body { font-size: 13px; color: var(--text-secondary); display: block; margin-top: 2px; }
.notif-meta { font-size: 11px; color: var(--text-muted); margin-top: 4px; display: block; }
.unread-dot { width: 8px; height: 8px; background: var(--accent); border-radius: 50%; margin-top: 6px; flex-shrink: 0; }
</style>
