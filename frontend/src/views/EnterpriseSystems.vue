<template>
  <div class="enterprise-page">
    <section class="hero-panel glass">
      <div class="hero-copy">
        <span class="hero-kicker">Enterprise Hub</span>
        <h2><el-icon><OfficeBuilding /></el-icon> 企业系统中心</h2>
        <p>把 OA、Jira、QCN、MES、共享盘和内网工具集中到一个入口，适合多系统、多域名场景统一维护。</p>
      </div>
      <div class="hero-actions">
        <el-button @click="openBulkEditor">
          <el-icon><EditPen /></el-icon> 批量编辑
        </el-button>
        <el-button type="primary" @click="openCreate"><el-icon><Plus /></el-icon> 添加系统</el-button>
      </div>
    </section>

    <div class="overview-strip">
      <div class="overview-card glass">
        <span class="overview-label">启用系统</span>
        <strong>{{ sortedSystems.length }}</strong>
      </div>
      <div class="overview-card glass">
        <span class="overview-label">隐藏系统</span>
        <strong>{{ hiddenSystems.length }}</strong>
      </div>
      <div class="overview-card glass">
        <span class="overview-label">累计访问</span>
        <strong>{{ totalVisits }}</strong>
      </div>
    </div>

    <div class="page-toolbar glass">
      <el-input v-model="searchText" placeholder="搜索系统名、类型、域名" clearable>
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-switch v-model="showHidden" inline-prompt active-text="显示隐藏" inactive-text="只看启用" />
    </div>

    <div class="ent-grid-wrapper">
      <div class="ent-grid">
        <div v-for="system in filteredSystems" :key="system.id" class="system-card glass glass-hover" @click="openSystem(system)">
          <div class="system-card-top">
            <div class="system-icon">
              <img v-if="system.icon_url" :src="system.icon_url" />
              <el-icon v-else size="24"><Platform /></el-icon>
            </div>
            <div class="system-actions visible-actions">
              <el-button size="small" @click.stop="toggleSystem(system)">{{ system.is_enabled ? '隐藏' : '启用' }}</el-button>
              <el-button size="small" @click.stop="openEdit(system)"><el-icon><Edit /></el-icon></el-button>
              <el-button size="small" type="danger" @click.stop="handleDelete(system)"><el-icon><Delete /></el-icon></el-button>
            </div>
          </div>
          <div class="system-info">
            <div class="system-heading">
              <span class="system-name">{{ system.name }}</span>
              <el-tag size="small" effect="plain">{{ typeLabel(system.system_type) }}</el-tag>
            </div>
            <span class="system-url">{{ system.url }}</span>
            <p v-if="system.description" class="system-desc">{{ system.description }}</p>
          </div>
          <div class="system-footer">
            <span class="visit-count">访问 {{ system.visit_count || 0 }} 次</span>
            <span class="system-status" :class="system.is_enabled ? 'is-on' : 'is-off'">
              {{ system.is_enabled ? '已启用' : '已隐藏' }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Hidden -->
    <div v-if="hiddenSystems.length && !showHidden" class="hidden-panel glass">
      <span class="text-sm text-secondary">已隐藏的系统:</span>
      <div class="hidden-list">
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

    <el-dialog v-model="showBulkEditor" title="批量编辑企业系统" width="860px" top="5vh">
      <div class="bulk-tip">
        适合集中维护 NAS、MES、ERP、QCN、Jira 等大量企业入口。保存时会新增或更新当前 JSON 中的条目，不会自动删除未列出的旧数据。
      </div>
      <el-input
        v-model="bulkEditorText"
        type="textarea"
        :rows="22"
        placeholder="[{ id, name, url, system_type, description, icon_url, is_enabled, sort_order }]"
      />
      <template #footer>
        <el-button @click="showBulkEditor = false">取消</el-button>
        <el-button type="primary" :loading="bulkSaving" @click="applyBulkEditor">保存批量修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { getEnterpriseSystems, createEnterpriseSystem, updateEnterpriseSystem, deleteEnterpriseSystem, sortEnterpriseSystems, recordEnterpriseVisit } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const systems = ref<any[]>([])
const showDialog = ref(false)
const editing = ref<any>(null)
const form = reactive({ name: '', url: '', system_type: 'other', description: '', icon_url: '' })
const searchText = ref('')
const showHidden = ref(false)
const showBulkEditor = ref(false)
const bulkEditorText = ref('')
const bulkSaving = ref(false)

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
const totalVisits = computed(() => systems.value.reduce((sum, system) => sum + (system.visit_count || 0), 0))
const filteredSystems = computed(() => {
  const keyword = searchText.value.trim().toLowerCase()
  const source = showHidden.value
    ? [...systems.value].sort((a, b) => a.sort_order - b.sort_order)
    : sortedSystems.value

  if (!keyword) return source
  return source.filter((system) => {
    const name = String(system.name || '').toLowerCase()
    const type = String(typeLabel(system.system_type) || '').toLowerCase()
    const url = String(system.url || '').toLowerCase()
    return name.includes(keyword) || type.includes(keyword) || url.includes(keyword)
  })
})

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

function openBulkEditor() {
  bulkEditorText.value = JSON.stringify(
    [...systems.value]
      .sort((a, b) => a.sort_order - b.sort_order)
      .map((system, index) => ({
        id: system.id,
        name: system.name,
        url: system.url,
        system_type: system.system_type,
        description: system.description,
        icon_url: system.icon_url,
        is_enabled: system.is_enabled,
        sort_order: Number.isFinite(Number(system.sort_order)) ? Number(system.sort_order) : index,
      })),
    null,
    2,
  )
  showBulkEditor.value = true
}

async function applyBulkEditor() {
  let parsed: any[]
  try {
    parsed = JSON.parse(bulkEditorText.value)
    if (!Array.isArray(parsed)) {
      throw new Error('JSON 顶层必须是数组')
    }
  } catch (error: any) {
    ElMessage.error(error?.message || 'JSON 格式不正确')
    return
  }

  bulkSaving.value = true
  try {
    const existingIds = new Set(systems.value.map((system) => system.id))

    for (let index = 0; index < parsed.length; index += 1) {
      const system = parsed[index]
      const payload = {
        name: String(system.name || '').trim(),
        url: String(system.url || '').trim(),
        system_type: String(system.system_type || 'other').trim() || 'other',
        description: String(system.description || ''),
        icon_url: String(system.icon_url || ''),
        is_enabled: typeof system.is_enabled === 'boolean' ? system.is_enabled : true,
        sort_order: Number.isFinite(Number(system.sort_order)) ? Number(system.sort_order) : index,
      }
      if (!payload.name || !payload.url) continue

      const systemId = Number(system.id)
      if (existingIds.has(systemId)) {
        await updateEnterpriseSystem(systemId, payload)
      } else {
        await createEnterpriseSystem(payload)
      }
    }

    await fetchData()
    showBulkEditor.value = false
    ElMessage.success('企业系统已批量更新')
  } catch {
    ElMessage.error('批量保存失败，请检查字段内容')
  } finally {
    bulkSaving.value = false
  }
}

onMounted(fetchData)
</script>

<style scoped>
.enterprise-page { max-width: 1180px; margin: 0 auto; }
.hero-panel { display: flex; align-items: center; justify-content: space-between; gap: 24px; padding: 28px; margin-bottom: 18px; background: linear-gradient(135deg, rgba(15, 23, 42, 0.9), rgba(8, 145, 178, 0.78)); color: #fff; }
.hero-kicker { display: inline-block; margin-bottom: 8px; padding: 4px 10px; border-radius: 999px; background: rgba(255, 255, 255, 0.16); font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; }
.hero-copy h2 { display: flex; align-items: center; gap: 10px; margin: 0 0 8px; font-size: 28px; font-weight: 800; }
.hero-copy p { max-width: 720px; margin: 0; color: rgba(255, 255, 255, 0.82); line-height: 1.7; }
.hero-actions { display: flex; gap: 10px; align-items: center; }
.overview-strip { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin-bottom: 18px; }
.overview-card { padding: 18px 20px; }
.overview-label { display: block; margin-bottom: 8px; color: var(--text-secondary); font-size: 13px; }
.overview-card strong { font-size: 28px; line-height: 1; }
.page-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 14px 16px; margin-bottom: 18px; }
.page-toolbar .el-input { max-width: 360px; }
.system-card { display: flex; flex-direction: column; gap: 14px; padding: 18px; min-height: 220px; cursor: pointer; }
.system-card-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
.system-icon { width: 52px; height: 52px; border-radius: 16px; background: linear-gradient(135deg, #0f766e, #2563eb); display: flex; align-items: center; justify-content: center; color: white; flex-shrink: 0; box-shadow: 0 12px 28px rgba(37, 99, 235, 0.2); }
.system-icon img { width: 28px; height: 28px; border-radius: 8px; }
.system-info { flex: 1; display: flex; flex-direction: column; gap: 8px; min-width: 0; }
.system-heading { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.system-name { font-size: 18px; font-weight: 800; }
.system-url { font-size: 13px; color: var(--text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.system-desc { margin: 0; color: var(--text-secondary); font-size: 13px; line-height: 1.6; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.system-footer { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-top: auto; }
.visit-count { font-size: 12px; color: var(--text-muted); }
.system-actions { display: flex; gap: 6px; }
.visible-actions { opacity: 1; }
.system-status { padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; }
.system-status.is-on { background: rgba(16, 185, 129, 0.12); color: #059669; }
.system-status.is-off { background: rgba(148, 163, 184, 0.16); color: #64748b; }
.hidden-panel { margin-top: 18px; padding: 16px; }
.hidden-list { display: flex; gap: 8px; margin-top: 12px; flex-wrap: wrap; }
.hidden-chip { padding: 6px 12px; background: var(--bg-primary); border-radius: 20px; font-size: 12px; cursor: pointer; opacity: 0.75; }
.hidden-chip:hover { opacity: 1; }
.ent-grid-wrapper .ent-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 14px;
}
.bulk-tip {
  margin-bottom: 12px;
  padding: 12px 14px;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(15, 118, 110, 0.08), rgba(59, 130, 246, 0.08));
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.6;
}

@media (max-width: 900px) {
  .hero-panel,
  .page-toolbar { flex-direction: column; align-items: stretch; }
  .overview-strip { grid-template-columns: 1fr; }
  .page-toolbar .el-input { max-width: none; }
}
</style>
