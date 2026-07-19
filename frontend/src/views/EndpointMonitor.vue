<template>
  <div class="endpoint-monitor">
    <div class="page-header">
      <h2><el-icon><Odometer /></el-icon> 端点监控</h2>
      <div class="header-actions">
        <el-button @click="checkAll" :loading="checkingAll"><el-icon><Refresh /></el-icon> 检测全部</el-button>
        <el-button type="primary" @click="openCreate"><el-icon><Plus /></el-icon> 添加端点</el-button>
      </div>
    </div>

    <div v-loading="loading" class="endpoint-grid">
      <div v-for="ep in endpoints" :key="ep.id" class="ep-card glass">
        <div class="ep-header">
          <span :class="['ep-status', ep.last_status]"></span>
          <span class="ep-name">{{ ep.name }}</span>
          <el-tag :type="ep.last_status === 'up' ? 'success' : ep.last_status === 'down' ? 'danger' : 'info'" size="small">
            {{ ep.last_status === 'up' ? '正常' : ep.last_status === 'down' ? '异常' : '未知' }}
          </el-tag>
          <el-switch :model-value="ep.is_enabled" @change="v => toggleEp(ep, v)" size="small" />
        </div>
        <div class="ep-url">{{ ep.url }}</div>
        <div class="ep-stats">
          <div class="ep-stat"><span class="label">响应</span><span>{{ ep.last_response_ms }}ms</span></div>
          <div class="ep-stat"><span class="label">可用率</span><span>{{ ep.uptime_percent }}%</span></div>
          <div class="ep-stat"><span class="label">检查次数</span><span>{{ ep.total_checks }}</span></div>
          <div class="ep-stat"><span class="label">失败次数</span><span :class="{ 'text-danger': ep.total_failures > 0 }">{{ ep.total_failures }}</span></div>
        </div>
        <div class="ep-footer">
          <span class="text-xs text-muted" v-if="ep.last_checked">上次检查: {{ formatDate(ep.last_checked) }}</span>
          <div class="ep-actions">
            <el-button size="small" @click="checkOne(ep)"><el-icon><Refresh /></el-icon></el-button>
            <el-button size="small" @click="openEdit(ep)"><el-icon><Edit /></el-icon></el-button>
            <el-button size="small" type="danger" @click="handleDelete(ep)"><el-icon><Delete /></el-icon></el-button>
          </div>
        </div>
      </div>
      <el-empty v-if="!loading && !endpoints.length" description="暂无监控端点" />
    </div>

    <el-dialog v-model="showDialog" :title="editing ? '编辑端点' : '添加端点'" width="500px">
      <el-form :model="form" label-position="top">
        <el-form-item label="名称 *"><el-input v-model="form.name" placeholder="如: 公司官网" /></el-form-item>
        <el-form-item label="URL *"><el-input v-model="form.url" placeholder="https://example.com" /></el-form-item>
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="方法"><el-select v-model="form.method" style="width:100%"><el-option v-for="m in ['GET','POST','HEAD']" :key="m" :value="m" /></el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="期望状态码"><el-input-number v-model="form.expected_code" :min="100" :max="599" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="间隔(秒)"><el-input-number v-model="form.interval_seconds" :min="30" :max="86400" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="超时(秒)"><el-input-number v-model="form.timeout_seconds" :min="1" :max="60" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer><el-button @click="showDialog = false">取消</el-button><el-button type="primary" @click="handleSave">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import api from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const endpoints = ref<any[]>([])
const loading = ref(false)
const checkingAll = ref(false)
const showDialog = ref(false)
const editing = ref<any>(null)
const form = reactive({ name: '', url: '', method: 'GET', expected_code: 200, interval_seconds: 300, timeout_seconds: 10, is_enabled: true })

async function fetchEndpoints() { loading.value = true; try { const { data } = await api.get('/monitoring/endpoints'); endpoints.value = data } catch { /* */ }; loading.value = false }
async function checkOne(ep: any) { await api.post(`/monitoring/endpoints/${ep.id}/check`); fetchEndpoints() }
async function checkAll() { checkingAll.value = true; await api.post('/monitoring/check-all'); fetchEndpoints(); checkingAll.value = false }
async function toggleEp(ep: any, v: boolean) { await api.put(`/monitoring/endpoints/${ep.id}`, { is_enabled: v }); fetchEndpoints() }

function openCreate() { editing.value = null; form.name = ''; form.url = ''; form.method = 'GET'; form.expected_code = 200; form.interval_seconds = 300; form.timeout_seconds = 10; showDialog.value = true }
function openEdit(ep: any) { editing.value = ep; Object.assign(form, ep); showDialog.value = true }
async function handleSave() {
  if (!form.name || !form.url) return
  if (editing.value) { await api.put(`/monitoring/endpoints/${editing.value.id}`, { ...form }); ElMessage.success('已更新') }
  else { await api.post('/monitoring/endpoints', { ...form }); ElMessage.success('已添加') }
  showDialog.value = false; fetchEndpoints()
}
async function handleDelete(ep: any) { try { await ElMessageBox.confirm(`删除 "${ep.name}"？`); await api.delete(`/monitoring/endpoints/${ep.id}`); fetchEndpoints() } catch { /* */ } }
function formatDate(d: string) { return new Date(d).toLocaleString('zh-CN') }

onMounted(fetchEndpoints)
</script>

<style scoped>
.endpoint-monitor { max-width: 1200px; margin: 0 auto; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.page-header h2 { display: flex; align-items: center; gap: 8px; font-size: 22px; font-weight: 800; }
.header-actions { display: flex; gap: 8px; }
.endpoint-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 12px; }
.ep-card { padding: 16px 18px; }
.ep-header { display: flex; align-items: center; gap: 8px; }
.ep-status { width: 8px; height: 8px; border-radius: 50%; }
.ep-status.up { background: #00b894; box-shadow: 0 0 6px #00b89488; }
.ep-status.down { background: #e17055; box-shadow: 0 0 6px #e1705588; }
.ep-status.unknown { background: #b2bec3; }
.ep-name { font-size: 16px; font-weight: 600; flex: 1; }
.ep-url { font-size: 12px; color: var(--text-muted); margin: 6px 0 10px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ep-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
.ep-stat { text-align: center; }
.ep-stat .label { display: block; font-size: 10px; color: var(--text-muted); }
.ep-stat span:last-child { font-size: 14px; font-weight: 600; }
.text-danger { color: #e17055; }
.ep-footer { display: flex; align-items: center; justify-content: space-between; margin-top: 10px; }
.ep-actions { display: flex; gap: 2px; opacity: 0; transition: opacity 0.2s; }
.ep-card:hover .ep-actions { opacity: 1; }
</style>
