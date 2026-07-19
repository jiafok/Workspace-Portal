<template>
  <div class="webhook-page">
    <div class="page-header">
      <h2><el-icon><Link /></el-icon> Webhook 管理</h2>
      <el-button type="primary" @click="openCreate"><el-icon><Plus /></el-icon> 添加 Webhook</el-button>
    </div>

    <el-alert title="当系统中的事件发生时（如新增网站、容器状态变化），自动向配置的 URL 发送通知" type="info" :closable="false" class="mb-4" />

    <div class="webhook-list">
      <div v-for="wh in webhooks" :key="wh.id" class="wh-card glass">
        <div class="wh-header">
          <span class="wh-name">{{ wh.name }}</span>
          <el-switch :model-value="wh.is_enabled" @change="v => toggleWh(wh, v)" size="small" />
        </div>
        <div class="wh-url">{{ wh.url }}</div>
        <div class="wh-meta">
          <el-tag size="small">{{ eventLabel(wh.event_type) }}</el-tag>
          <span class="text-xs text-muted">触发 {{ wh.trigger_count }} 次</span>
          <span v-if="wh.last_triggered" class="text-xs text-muted">最后: {{ formatDate(wh.last_triggered) }}</span>
        </div>
        <div class="wh-actions">
          <el-button size="small" @click="testWh(wh)"><el-icon><Promotion /></el-icon> 测试</el-button>
          <el-button size="small" @click="openEdit(wh)"><el-icon><Edit /></el-icon></el-button>
          <el-button size="small" type="danger" @click="handleDelete(wh)"><el-icon><Delete /></el-icon></el-button>
        </div>
      </div>
      <el-empty v-if="!webhooks.length" description="暂无 Webhook" />
    </div>

    <el-dialog v-model="showDialog" :title="editing ? '编辑 Webhook' : '添加 Webhook'" width="500px">
      <el-form :model="form" label-position="top">
        <el-form-item label="名称 *"><el-input v-model="form.name" placeholder="如: 钉钉通知" /></el-form-item>
        <el-form-item label="URL *"><el-input v-model="form.url" placeholder="https://hooks.example.com/webhook" /></el-form-item>
        <el-form-item label="事件类型"><el-select v-model="form.event_type" style="width:100%"><el-option v-for="e in eventTypes" :key="e.value" :value="e.value" :label="e.label" /></el-select></el-form-item>
        <el-form-item label="密钥 (可选)"><el-input v-model="form.secret" placeholder="用于 HMAC 签名验证" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="showDialog = false">取消</el-button><el-button type="primary" @click="handleSave">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import api from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const webhooks = ref<any[]>([])
const showDialog = ref(false)
const editing = ref<any>(null)
const form = reactive({ name: '', url: '', event_type: 'all', secret: '' })

const eventTypes = [
  { value: 'all', label: '全部事件' }, { value: 'navigation', label: '导航变更' },
  { value: 'docker', label: 'Docker 事件' }, { value: 'system', label: '系统事件' },
  { value: 'custom', label: '自定义' },
]

function eventLabel(t: string) { return eventTypes.find(e => e.value === t)?.label || t }

async function fetchData() { const { data } = await api.get('/webhooks'); webhooks.value = data }
async function toggleWh(wh: any, v: boolean) { await api.put(`/webhooks/${wh.id}`, { is_enabled: v }); fetchData() }
async function testWh(wh: any) { await api.post(`/webhooks/${wh.id}/test`); ElMessage.success('测试请求已发送') }

function openCreate() { editing.value = null; form.name = ''; form.url = ''; form.event_type = 'all'; form.secret = ''; showDialog.value = true }
function openEdit(wh: any) { editing.value = wh; Object.assign(form, wh); showDialog.value = true }
async function handleSave() {
  if (!form.name || !form.url) return
  if (editing.value) { await api.put(`/webhooks/${editing.value.id}`, { ...form }); ElMessage.success('已更新') }
  else { await api.post('/webhooks', { ...form }); ElMessage.success('已添加') }
  showDialog.value = false; fetchData()
}
async function handleDelete(wh: any) { try { await ElMessageBox.confirm(`删除 "${wh.name}"？`); await api.delete(`/webhooks/${wh.id}`); fetchData() } catch { /* */ } }
function formatDate(d: string) { return new Date(d).toLocaleString('zh-CN') }

onMounted(fetchData)
</script>

<style scoped>
.webhook-page { max-width: 900px; margin: 0 auto; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.page-header h2 { display: flex; align-items: center; gap: 8px; font-size: 22px; font-weight: 800; }
.webhook-list { display: flex; flex-direction: column; gap: 10px; }
.wh-card { padding: 16px 20px; }
.wh-header { display: flex; align-items: center; justify-content: space-between; }
.wh-name { font-size: 16px; font-weight: 700; }
.wh-url { font-size: 13px; color: var(--text-muted); margin: 6px 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.wh-meta { display: flex; gap: 10px; align-items: center; margin-bottom: 8px; }
.wh-actions { display: flex; gap: 4px; opacity: 0; transition: opacity 0.2s; }
.wh-card:hover .wh-actions { opacity: 1; }
</style>
