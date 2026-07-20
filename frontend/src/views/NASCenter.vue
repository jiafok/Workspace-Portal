<template>
  <div class="nas-center">
    <div class="page-header">
      <h2><el-icon><Monitor /></el-icon> NAS 中心</h2>
      <el-button type="primary" @click="openCreate"><el-icon><Plus /></el-icon> 添加服务</el-button>
    </div>

    <el-alert title="点击服务卡片自动检测内网可达性，优先使用内网地址" type="info" :closable="false" class="mb-4" />

    <div class="nas-grid">
      <div v-for="svc in sortedServices" :key="svc.id" class="nas-card glass glass-hover" @click="openService(svc)">
        <div class="nas-top">
          <div class="nas-icon" :style="{ background: iconColor(svc.name) }">
            <span class="nas-letter">{{ svc.name[0] }}</span>
          </div>
          <div class="nas-info">
            <span class="nas-name">{{ svc.name }}</span>
            <span class="nas-status-badge" :class="svc._status?.includes('✓') ? 'ok' : svc._status?.includes('不通') ? 'fail' : ''">
              {{ svc._status || '点击检测' }}
            </span>
          </div>
          <div class="nas-actions">
            <el-button text size="small" @click.stop="openEdit(svc)"><el-icon><Edit /></el-icon></el-button>
            <el-button text size="small" @click.stop="handleDelete(svc)"><el-icon><Delete /></el-icon></el-button>
          </div>
        </div>
        <div class="nas-urls">
          <div class="url-row">
            <span class="url-label">🏠 内网</span>
            <span class="url-value">{{ svc.internal_url || '未设置' }}</span>
          </div>
          <div class="url-row">
            <span class="url-label">🌍 远程</span>
            <span class="url-value">{{ svc.external_url || '未设置' }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="hiddenServices.length" class="mt-4">
      <span class="text-sm text-secondary">已隐藏:</span>
      <div class="flex gap-2 mt-2 flex-wrap">
        <span v-for="s in hiddenServices" :key="s.id" class="hidden-chip" @click="toggleEnable(s)">{{ s.name }} (启用)</span>
      </div>
    </div>

    <el-dialog v-model="showAdd" :title="editingSvc ? '编辑服务' : '添加服务'" width="520px">
      <el-form :model="form" label-position="top">
        <el-form-item label="名称 *"><el-input v-model="form.name" placeholder="如: DSM" /></el-form-item>
        <el-form-item label="内网地址"><el-input v-model="form.internal_url" placeholder="192.168.0.115:5000"><template #prepend>http://</template></el-input></el-form-item>
        <el-form-item label="远程地址"><el-input v-model="form.external_url" placeholder="172.23.72.9:5000"><template #prepend>http://</template></el-input></el-form-item>
        <el-form-item label="图标URL"><el-input v-model="form.icon_url" placeholder="可选" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="showAdd=false">取消</el-button><el-button type="primary" @click="handleSave">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { getNASServices, createNASService, updateNASService, deleteNASService, recordNASVisit } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const services = ref<any[]>([])
const showAdd = ref(false)
const editingSvc = ref<any>(null)
const form = reactive({ name: '', internal_url: '', external_url: '', icon_url: '' })

const sortedServices = computed(() => services.value.filter(s => s.is_enabled).sort((a, b) => a.sort_order - b.sort_order))
const hiddenServices = computed(() => services.value.filter(s => !s.is_enabled))

function iconColor(name: string) {
  const colors = ['linear-gradient(135deg,#6c5ce7,#a29bfe)','linear-gradient(135deg,#00b894,#55efc4)','linear-gradient(135deg,#0984e3,#74b9ff)','linear-gradient(135deg,#e17055,#fab1a0)','linear-gradient(135deg,#fdcb6e,#ffeaa7)','linear-gradient(135deg,#fd79a8,#fab1a0)']
  let h = 0; for (const c of name) h += c.charCodeAt(0); return colors[h % colors.length]
}

async function fetchData() { const { data } = await getNASServices(); services.value = data.map((s: any) => ({ ...s, _status: '' })) }

async function openService(svc: any) {
  recordNASVisit(svc.id)
  const iUrl = svc.internal_url ? `http://${svc.internal_url}` : ''
  const eUrl = svc.external_url ? `http://${svc.external_url}` : ''
  if (iUrl) {
    try { svc._status = '检测中...'; const c = new AbortController(); const t = setTimeout(() => c.abort(), 3000); await fetch(iUrl, { mode: 'no-cors', signal: c.signal }); clearTimeout(t); svc._status = '内网 ✓'; window.open(iUrl, '_blank'); return }
    catch { svc._status = '内网不通' }
  }
  if (eUrl) { svc._status = '远程 ✓'; window.open(eUrl, '_blank') }
}

async function toggleEnable(s: any) { await updateNASService(s.id, { is_enabled: !s.is_enabled }); fetchData() }
function openCreate() { editingSvc.value = null; form.name=''; form.internal_url=''; form.external_url=''; form.icon_url=''; showAdd.value = true }
function openEdit(s: any) { editingSvc.value = s; form.name=s.name; form.internal_url=s.internal_url; form.external_url=s.external_url; form.icon_url=s.icon_url; showAdd.value = true }
async function handleSave() {
  if (!form.name) return
  if (editingSvc.value) { await updateNASService(editingSvc.value.id, { ...form }); ElMessage.success('已更新') }
  else { await createNASService({ ...form, is_enabled: true }); ElMessage.success('已添加') }
  showAdd.value = false; fetchData()
}
async function handleDelete(s: any) { try { await ElMessageBox.confirm(`删除 "${s.name}"？`); await deleteNASService(s.id); fetchData() } catch {} }

onMounted(fetchData)
</script>

<style scoped>
.nas-center { max-width: 1100px; margin: 0 auto; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.page-header h2 { display: flex; align-items: center; gap: 8px; font-size: 22px; font-weight: 800; }
.nas-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 12px; }
.nas-card { padding: 18px 20px; }
.nas-top { display: flex; align-items: center; gap: 14px; margin-bottom: 14px; }
.nas-icon { width: 48px; height: 48px; border-radius: 14px; display: flex; align-items: center; justify-content: center; color: white; flex-shrink: 0; }
.nas-letter { font-size: 22px; font-weight: 800; }
.nas-info { flex: 1; display: flex; flex-direction: column; gap: 4px; }
.nas-name { font-size: 16px; font-weight: 700; }
.nas-status-badge { font-size: 11px; padding: 2px 8px; border-radius: 4px; background: var(--bg-primary); color: var(--text-muted); width: fit-content; }
.nas-status-badge.ok { background: rgba(0,184,148,0.15); color: #00b894; }
.nas-status-badge.fail { background: rgba(225,112,85,0.15); color: #e17055; }
.nas-actions { display: flex; gap: 2px; opacity: 0; transition: opacity 0.2s; }
.nas-card:hover .nas-actions { opacity: 1; }
.nas-urls { display: flex; flex-direction: column; gap: 6px; }
.url-row { display: flex; align-items: center; gap: 8px; font-size: 12px; }
.url-label { color: var(--text-muted); flex-shrink: 0; width: 50px; }
.url-value { color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.hidden-chip { padding: 4px 12px; background: var(--bg-primary); border-radius: 20px; font-size: 12px; cursor: pointer; opacity: 0.6; }
.hidden-chip:hover { opacity: 1; }
</style>
