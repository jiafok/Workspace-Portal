<template>
  <div class="nas-center">
    <div class="page-header">
      <h2><el-icon><Monitor /></el-icon> NAS 中心</h2>
      <el-button type="primary" @click="showAdd = true">
        <el-icon><Plus /></el-icon> 添加服务
      </el-button>
    </div>

    <el-alert
      title="点击服务卡片将自动检测网络可达性，优先使用内网地址访问"
      type="info"
      :closable="false"
      style="margin-bottom:20px"
    />

    <draggable
      v-model="sortedServices"
      item-key="id"
      :animation="200"
      ghost-class="sortable-ghost"
      @change="onDragChange"
      class="svc-grid"
    >
      <template #item="{ element: svc }">
        <div v-if="svc.is_enabled" class="nas-card glass glass-hover" @click="openService(svc)">
          <div class="nas-icon">
            <img v-if="svc.icon_url" :src="svc.icon_url" />
            <span v-else class="nas-letter">{{ svc.name[0] }}</span>
          </div>
          <div class="nas-info">
            <span class="nas-name">{{ svc.name }}</span>
            <span class="nas-urls">
              <span class="url-tag internal">内网 {{ svc.internal_url || '未设置' }}</span>
              <span class="url-tag external">远程 {{ svc.external_url || '未设置' }}</span>
            </span>
            <span class="nas-status" :class="statusClass(svc)">
              {{ svc._status || '点击检测' }}
            </span>
          </div>
          <div class="nas-card-actions">
            <el-button text size="small" @click.stop="openEdit(svc)"><el-icon><Edit /></el-icon></el-button>
            <el-button text size="small" @click.stop="handleDelete(svc)"><el-icon><Delete /></el-icon></el-button>
          </div>
        </div>
      </template>
    </draggable>

    <!-- Hidden -->
    <div v-if="hiddenServices.length" class="section">
      <h3 class="section-label">👁 已隐藏</h3>
      <div class="hidden-list">
        <div v-for="svc in hiddenServices" :key="svc.id" class="hidden-item" @click="toggleEnable(svc)">
          <span>{{ svc.name }}</span>
          <span class="hidden-tip">点击启用</span>
        </div>
      </div>
    </div>

    <!-- Dialog -->
    <el-dialog v-model="showAdd" :title="editingSvc ? '编辑服务' : '添加服务'" width="520px">
      <el-form :model="form" label-position="top">
        <el-form-item label="名称 *">
          <el-input v-model="form.name" placeholder="如: DSM" />
        </el-form-item>
        <el-form-item label="内网地址">
          <el-input v-model="form.internal_url" placeholder="192.168.0.115:5000">
            <template #prepend>http://</template>
          </el-input>
        </el-form-item>
        <el-form-item label="远程地址">
          <el-input v-model="form.external_url" placeholder="172.23.72.9:5000">
            <template #prepend>http://</template>
          </el-input>
        </el-form-item>
        <el-form-item label="图标URL">
          <el-input v-model="form.icon_url" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAdd = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import {
  getNASServices, createNASService, updateNASService,
  deleteNASService, sortNASServices, recordNASVisit
} from '../api'
import draggable from 'vuedraggable'
import { ElMessage, ElMessageBox } from 'element-plus'

const services = ref<any[]>([])
const showAdd = ref(false)
const editingSvc = ref<any>(null)
const form = reactive({ name: '', internal_url: '', external_url: '', icon_url: '' })

const sortedServices = computed({
  get: () => services.value.filter(s => s.is_enabled).sort((a, b) => a.sort_order - b.sort_order),
  set: () => {},
})
const hiddenServices = computed(() => services.value.filter(s => !s.is_enabled))

async function fetchData() {
  const { data } = await getNASServices()
  services.value = data.map(s => ({ ...s, _status: '' }))
}

async function openService(svc: any) {
  recordNASVisit(svc.id)
  const internalUrl = svc.internal_url ? `http://${svc.internal_url}` : ''
  const externalUrl = svc.external_url ? `http://${svc.external_url}` : ''

  if (internalUrl) {
    try {
      svc._status = '检测中...'
      const controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), 3000)
      await fetch(internalUrl, { mode: 'no-cors', signal: controller.signal })
      clearTimeout(timeout)
      svc._status = '内网 ✓'
      window.open(internalUrl, '_blank')
      return
    } catch {
      svc._status = '内网不通'
    }
  }

  if (externalUrl) {
    svc._status = '使用远程'
    window.open(externalUrl, '_blank')
  }
}

function statusClass(svc: any) {
  if (svc._status?.includes('✓')) return 'ok'
  if (svc._status?.includes('不通')) return 'fail'
  return ''
}

async function toggleEnable(svc: any) {
  await updateNASService(svc.id, { is_enabled: !svc.is_enabled })
  await fetchData()
}

function openEdit(svc: any) {
  editingSvc.value = svc
  form.name = svc.name
  form.internal_url = svc.internal_url
  form.external_url = svc.external_url
  form.icon_url = svc.icon_url
  showAdd.value = true
}

async function handleSave() {
  if (!form.name) return
  if (editingSvc.value) {
    await updateNASService(editingSvc.value.id, { ...form })
    ElMessage.success('已更新')
  } else {
    await createNASService({ ...form, is_enabled: true })
    ElMessage.success('已添加')
  }
  showAdd.value = false
  editingSvc.value = null
  form.name = ''; form.internal_url = ''; form.external_url = ''; form.icon_url = ''
  await fetchData()
}

async function handleDelete(svc: any) {
  try {
    await ElMessageBox.confirm(`确定删除 "${svc.name}"？`, '确认', { type: 'warning' })
    await deleteNASService(svc.id)
    ElMessage.success('已删除')
    await fetchData()
  } catch { /* cancelled */ }
}

async function onDragChange() {
  const items = sortedServices.value.map((s: any, i: number) => ({ id: s.id, sort_order: i }))
  await sortNASServices(items)
}

onMounted(fetchData)
</script>

<style scoped>
.nas-center {
  max-width: 1000px;
  margin: 0 auto;
}
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.page-header h2 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 22px;
  font-weight: 800;
}
.nas-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 18px 20px;
  margin-bottom: 10px;
  cursor: pointer;
}
.nas-icon {
  width: 50px;
  height: 50px;
  border-radius: 14px;
  background: var(--accent-gradient);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.nas-letter {
  color: white;
  font-size: 22px;
  font-weight: 800;
}
.nas-icon img {
  width: 30px;
  height: 30px;
}
.nas-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.nas-name {
  font-size: 16px;
  font-weight: 700;
}
.nas-urls {
  display: flex;
  gap: 8px;
}
.url-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
}
.url-tag.internal {
  background: rgba(108, 92, 231, 0.1);
  color: var(--accent);
}
.url-tag.external {
  background: rgba(0, 184, 148, 0.1);
  color: #00b894;
}
.nas-status {
  font-size: 12px;
  color: var(--text-muted);
}
.nas-status.ok { color: #00b894; }
.nas-status.fail { color: #e17055; }
.nas-card-actions {
  opacity: 0;
  transition: opacity var(--transition);
}
.nas-card:hover .nas-card-actions {
  opacity: 1;
}
.section {
  margin-top: 16px;
}
.section-label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}
.hidden-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.hidden-item {
  padding: 8px 16px;
  border-radius: 20px;
  background: var(--bg-primary);
  cursor: pointer;
  font-size: 13px;
  opacity: 0.6;
  display: flex;
  gap: 8px;
  align-items: center;
}
.hidden-item:hover {
  opacity: 1;
}
.hidden-tip {
  font-size: 11px;
  color: var(--text-muted);
}
.svc-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 10px;
}
.svc-grid > div { display: contents; }
</style>
