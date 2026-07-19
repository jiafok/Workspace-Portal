<template>
  <div class="audit-log-page">
    <div class="page-header">
      <h2><el-icon><DocumentChecked /></el-icon> 审计日志</h2>
      <div class="header-actions">
        <el-select v-model="filterAction" placeholder="操作类型" clearable size="default" style="width:140px">
          <el-option v-for="a in actionTypes" :key="a" :value="a" :label="actionLabel(a)" />
        </el-select>
      </div>
    </div>

    <div class="log-list">
      <div v-for="log in filteredLogs" :key="log.id" class="log-item glass">
        <div class="log-icon" :class="log.action">
          <el-icon size="14"><component :is="actionIcon(log.action)" /></el-icon>
        </div>
        <div class="log-main">
          <span class="log-user">{{ log.username || '系统' }}</span>
          <span class="log-action">{{ actionLabel(log.action) }}</span>
          <span v-if="log.resource_type" class="log-resource">{{ log.resource_type }}</span>
          <span v-if="log.resource_name" class="log-name">{{ log.resource_name }}</span>
        </div>
        <span class="log-time">{{ formatDate(log.created_at) }}</span>
      </div>
      <el-empty v-if="!filteredLogs.length" description="暂无审计记录" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '../api'

const logs = ref<any[]>([])
const filterAction = ref('')

const actionTypes = ['create', 'update', 'delete', 'login', 'logout']

const filteredLogs = computed(() => {
  if (!filterAction.value) return logs.value
  return logs.value.filter(l => l.action === filterAction.value)
})

function actionLabel(a: string) {
  const m: Record<string, string> = { create: '创建', update: '修改', delete: '删除', login: '登录', logout: '登出' }
  return m[a] || a
}
function actionIcon(a: string) {
  const m: Record<string, string> = { create: 'Plus', update: 'Edit', delete: 'Delete', login: 'User', logout: 'SwitchButton' }
  return m[a] || 'InfoFilled'
}
function formatDate(d: string) { return new Date(d).toLocaleString('zh-CN') }

onMounted(async () => {
  try { const { data } = await api.get('/monitoring/audit-logs', { params: { limit: 200 } }); logs.value = data } catch { /* */ }
})
</script>

<style scoped>
.audit-log-page { max-width: 1000px; margin: 0 auto; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.page-header h2 { display: flex; align-items: center; gap: 8px; font-size: 22px; font-weight: 800; }
.log-list { display: flex; flex-direction: column; gap: 4px; }
.log-item { display: flex; align-items: center; gap: 12px; padding: 12px 16px; font-size: 13px; }
.log-icon { width: 28px; height: 28px; border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.log-icon.create { background: #00b89422; color: #00b894; }
.log-icon.update { background: #0984e322; color: #0984e3; }
.log-icon.delete { background: #e1705522; color: #e17055; }
.log-icon.login { background: #6c5ce722; color: #6c5ce7; }
.log-icon.logout { background: #636e7222; color: #636e72; }
.log-main { flex: 1; display: flex; gap: 6px; flex-wrap: wrap; align-items: center; }
.log-user { font-weight: 600; }
.log-action { color: var(--text-secondary); }
.log-resource { color: var(--text-muted); font-size: 11px; background: var(--bg-primary); padding: 1px 8px; border-radius: 4px; }
.log-name { font-weight: 500; }
.log-time { font-size: 11px; color: var(--text-muted); white-space: nowrap; }
</style>
