<template>
  <div class="enterprise-page">
    <div class="page-header">
      <h2><el-icon><OfficeBuilding /></el-icon> 企业系统中心</h2>
      <el-button type="primary" @click="openCreate"><el-icon><Plus /></el-icon> 添加系统</el-button>
    </div>

    <div class="ent-grid-wrapper">
      <draggable v-model="sortedSystems" item-key="id" :animation="200" ghost-class="sortable-ghost" @change="onDragChange" handle=".drag-handle" class="ent-grid">
        <template #item="{ element: system }">
          <div v-if="system.is_enabled" class="system-card glass glass-hover" @click="openSystem(system)">
            <div class="drag-handle"><el-icon size="14"><Rank /></el-icon></div>
            <div class="system-icon">
              <img v-if="system.icon_url" :src="system.icon_url" />
              <el-icon v-else size="24"><Platform /></el-icon>
            </div>
            <div class="system-info">
              <span class="system-name">{{ system.name }}</span>
              <span class="system-type">
                <el-tag size="small">{{ typeLabel(system.system_type) }}</el-tag>
              </span>
              <span class="system-url">{{ system.url }}</span>
            </div>
            <div class="system-right">
              <span class="visit-count">访问 {{ system.visit_count }} 次</span>
              <div class="system-actions">
                <el-button size="small" @click.stop="openEdit(system)"><el-icon><Edit /></el-icon></el-button>
                <el-button size="small" type="danger" @click.stop="handleDelete(system)"><el-icon><Delete /></el-icon></el-button>
              </div>
            </div>
          </div>
        </template>
      </draggable>
    </div>

    <!-- Hidden -->
    <div v-if="hiddenSystems.length" class="mt-4">
      <span class="text-sm text-secondary">已隐藏的系统:</span>
      <div class="flex gap-2 mt-2 flex-wrap">
        <span v-for="s in hiddenSystems" :key="s.id" class="hidden-chip" @click="toggleSystem(s)">
          {{ s.name }} (点击启用)
        </span>
      </div>
    </div>

    <el-dialog v-model="showDialog" :title="editing ? '编辑企业系统' : '添加企业系统'" width="500px">
      <el-form :model="form" label-position="top">
        <el-form-item label="名称 *">
          <el-input v-model="form.name" placeholder="如: Jira" />
        </el-form-item>
        <el-form-item label="URL *">
          <el-input v-model="form.url" placeholder="https://jira.example.com" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="form.system_type" style="width:100%">
            <el-option v-for="t in systemTypes" :key="t.value" :value="t.value" :label="t.label" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="图标URL">
          <el-input v-model="form.icon_url" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { getEnterpriseSystems, createEnterpriseSystem, updateEnterpriseSystem, deleteEnterpriseSystem, sortEnterpriseSystems, recordEnterpriseVisit } from '../api'
import draggable from 'vuedraggable'
import { ElMessage, ElMessageBox } from 'element-plus'

const systems = ref<any[]>([])
const showDialog = ref(false)
const editing = ref<any>(null)
const form = reactive({ name: '', url: '', system_type: 'other', description: '', icon_url: '' })

const systemTypes = [
  { value: 'eip', label: 'EIP' }, { value: 'bpm', label: 'BPM' }, { value: 'hr', label: 'HR系统' },
  { value: 'sharepoint', label: 'SharePoint' }, { value: 'onedrive', label: 'OneDrive' },
  { value: 'outlook', label: 'Outlook' }, { value: 'teams', label: 'Teams' },
  { value: 'jira', label: 'Jira' }, { value: 'confluence', label: 'Confluence' },
  { value: 'devops', label: 'DevOps' }, { value: 'it_ticket', label: 'IT工单' },
  { value: 'eservice', label: 'E-Service' }, { value: 'qcn', label: 'QCN查询' },
  { value: 'imei', label: 'IMEI查询' }, { value: 'other', label: '其他' },
]

const sortedSystems = computed({
  get: () => systems.value.filter(s => s.is_enabled).sort((a, b) => a.sort_order - b.sort_order),
  set: () => {},
})
const hiddenSystems = computed(() => systems.value.filter(s => !s.is_enabled))

function typeLabel(t: string) { return systemTypes.find(st => st.value === t)?.label || t }

async function fetchData() { const { data } = await getEnterpriseSystems(); systems.value = data }

function openSystem(s: any) { recordEnterpriseVisit(s.id); window.open(s.url, '_blank') }
async function toggleSystem(s: any) {
  await updateEnterpriseSystem(s.id, { is_enabled: !s.is_enabled }); fetchData()
}

function openCreate() { editing.value = null; form.name = ''; form.url = ''; form.system_type = 'other'; form.description = ''; form.icon_url = ''; showDialog.value = true }
function openEdit(s: any) { editing.value = s; form.name = s.name; form.url = s.url; form.system_type = s.system_type; form.description = s.description; form.icon_url = s.icon_url; showDialog.value = true }

async function handleSave() {
  if (!form.name || !form.url) return
  if (editing.value) { await updateEnterpriseSystem(editing.value.id, { ...form }); ElMessage.success('已更新') }
  else { await createEnterpriseSystem({ ...form, is_enabled: true }); ElMessage.success('已添加') }
  showDialog.value = false; fetchData()
}

async function handleDelete(s: any) {
  try { await ElMessageBox.confirm(`删除 "${s.name}"？`, '确认', { type: 'warning' }); await deleteEnterpriseSystem(s.id); ElMessage.success('已删除'); fetchData() }
  catch { /* */ }
}

async function onDragChange() {
  const items = sortedSystems.value.map((s: any, i: number) => ({ id: s.id, sort_order: i }))
  await sortEnterpriseSystems(items)
}

onMounted(fetchData)
</script>

<style scoped>
.enterprise-page { max-width: 1000px; margin: 0 auto; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.page-header h2 { display: flex; align-items: center; gap: 8px; font-size: 22px; font-weight: 800; }
.system-card { display: flex; align-items: center; gap: 14px; padding: 16px 18px; margin-bottom: 8px; cursor: pointer; }
.drag-handle { cursor: grab; color: var(--text-muted); flex-shrink: 0; }
.system-icon { width: 44px; height: 44px; border-radius: 12px; background: var(--accent-gradient); display: flex; align-items: center; justify-content: center; color: white; flex-shrink: 0; }
.system-icon img { width: 24px; height: 24px; border-radius: 4px; }
.system-info { flex: 1; display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.system-name { font-size: 16px; font-weight: 700; }
.system-url { font-size: 12px; color: var(--text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.system-right { text-align: right; }
.visit-count { font-size: 11px; color: var(--text-muted); display: block; margin-bottom: 4px; }
.system-actions { display: flex; gap: 2px; opacity: 0; transition: opacity 0.2s; }
.system-card:hover .system-actions { opacity: 1; }
.hidden-chip { padding: 4px 12px; background: var(--bg-primary); border-radius: 20px; font-size: 12px; cursor: pointer; opacity: 0.6; }
.hidden-chip:hover { opacity: 1; }
.ent-grid-wrapper .ent-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 8px;
}
.ent-grid-wrapper .ent-grid > div { display: contents; }
</style>
