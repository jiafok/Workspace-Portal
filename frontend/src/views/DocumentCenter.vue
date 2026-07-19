<template>
  <div class="doc-center">
    <div class="page-header">
      <h2><el-icon><Files /></el-icon> 文档中心</h2>
      <el-button type="primary" @click="showAddSource = true"><el-icon><Plus /></el-icon> 添加文档源</el-button>
    </div>

    <!-- Sources -->
    <div class="sources-row mb-4">
      <div v-for="src in sources" :key="src.id" :class="['source-tab', { active: selectedSource === src.id }]" @click="selectSource(src)">
        <el-icon><component :is="sourceIcon(src.source_type)" /></el-icon>
        <span>{{ src.name }}</span>
        <el-tag size="small">{{ src.source_type }}</el-tag>
      </div>
    </div>

    <!-- Files -->
    <div v-if="selectedSource" class="files-section">
      <div class="files-header glass">
        <el-input v-model="fileSearch" placeholder="搜索文件..." style="width:250px" size="default" clearable>
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-button @click="syncFiles" :loading="syncing">
          <el-icon><Refresh /></el-icon> 同步 SharePoint
        </el-button>
      </div>

      <div v-if="filteredFiles.length" class="file-list">
        <div v-for="file in filteredFiles" :key="file.id" class="file-item glass glass-hover" @click="openFile(file)">
          <el-icon size="20" :color="fileIconColor(file.file_type)"><Document /></el-icon>
          <div class="file-info">
            <span class="file-name">{{ file.name }}</span>
            <span class="file-meta">
              {{ formatSize(file.size) }} · {{ file.modified_by }} · {{ formatDate(file.last_modified) }}
            </span>
          </div>
          <el-button text size="small" @click.stop="toggleFav(file)">
            <el-icon :color="file.is_favorite ? '#fdcb6e' : ''"><StarFilled v-if="file.is_favorite" /><Star v-else /></el-icon>
          </el-button>
        </div>
      </div>
      <el-empty v-else description="暂无文件，配置 SharePoint 源并同步" />
    </div>

    <!-- Add Source Dialog -->
    <el-dialog v-model="showAddSource" title="添加文档源" width="500px">
      <el-form :model="sourceForm" label-position="top">
        <el-form-item label="名称 *">
          <el-input v-model="sourceForm.name" placeholder="如: 团队 SharePoint" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="sourceForm.source_type" style="width:100%">
            <el-option value="sharepoint" label="SharePoint" />
            <el-option value="onedrive" label="OneDrive" />
            <el-option value="quecilb" label="QuecLib" />
            <el-option value="custom" label="自定义" />
          </el-select>
        </el-form-item>
        <el-form-item label="URL">
          <el-input v-model="sourceForm.url" placeholder="https://tenant.sharepoint.com/sites/xxx" />
        </el-form-item>
        <el-form-item label="Site ID">
          <el-input v-model="sourceForm.site_id" placeholder="SharePoint Site ID" />
        </el-form-item>
        <el-form-item label="Drive ID">
          <el-input v-model="sourceForm.drive_id" placeholder="文档库 Drive ID" />
        </el-form-item>
        <el-form-item label="文件夹路径">
          <el-input v-model="sourceForm.folder_path" placeholder="/Shared Documents" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddSource = false">取消</el-button>
        <el-button type="primary" @click="handleAddSource">添加</el-button>
      </template>
    </el-dialog>

    <!-- Sync notice -->
    <el-dialog v-model="showSyncInfo" title="SharePoint 同步配置" width="550px">
      <el-alert type="info" :closable="false" class="mb-4">
        <p>要启用实时 SharePoint 文件同步，请配置以下信息：</p>
      </el-alert>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="需要配置">Microsoft Graph API 访问权限</el-descriptions-item>
        <el-descriptions-item label="Azure AD 应用">需注册应用并授予 Files.Read.All 权限</el-descriptions-item>
        <el-descriptions-item label="配置位置">系统设置 → OAuth 配置 → Azure AD / OIDC</el-descriptions-item>
        <el-descriptions-item label="API 地址">https://graph.microsoft.com/v1.0</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import {
  getDocumentSources, createDocumentSource, deleteDocumentSource,
  getSharePointFiles, syncSharePoint, toggleFileFavorite, searchSharePoint
} from '../api'
import { ElMessage } from 'element-plus'

const sources = ref<any[]>([])
const files = ref<any[]>([])
const selectedSource = ref<number | null>(null)
const fileSearch = ref('')
const syncing = ref(false)
const showAddSource = ref(false)
const showSyncInfo = ref(false)
const sourceForm = reactive({ name: '', source_type: 'sharepoint', url: '', site_id: '', drive_id: '', folder_path: '' })

const filteredFiles = computed(() => {
  if (!fileSearch.value) return files.value
  return files.value.filter((f: any) => f.name.toLowerCase().includes(fileSearch.value.toLowerCase()))
})

function sourceIcon(type: string) {
  const map: Record<string, string> = { sharepoint: 'Platform', onedrive: 'FolderOpened', quecilb: 'Notebook', custom: 'Folder' }
  return map[type] || 'Folder'
}
function fileIconColor(type: string) {
  const map: Record<string, string> = { xlsx: '#00b894', xls: '#00b894', docx: '#0984e3', doc: '#0984e3', pptx: '#e17055', ppt: '#e17055', pdf: '#d63031' }
  return map[type] || 'var(--text-muted)'
}
function formatSize(b: number) { if (!b) return '0KB'; return b < 1024 * 1024 ? Math.round(b / 1024) + 'KB' : (b / (1024 * 1024)).toFixed(1) + 'MB' }
function formatDate(d: string | null) { if (!d) return ''; return new Date(d).toLocaleDateString('zh-CN') }

async function fetchSources() { const { data } = await getDocumentSources(); sources.value = data }

async function selectSource(src: any) {
  selectedSource.value = src.id
  try {
    const { data } = await getSharePointFiles(src.id)
    files.value = data
  } catch { files.value = [] }
}

async function syncFiles() {
  if (!selectedSource.value) return
  syncing.value = true
  try {
    const result = await syncSharePoint(selectedSource.value)
    if (result.data.message) showSyncInfo.value = true
    await selectSource({ id: selectedSource.value })
    ElMessage.success('同步完成')
  } catch { ElMessage.error('同步失败') }
  syncing.value = false
}

function openFile(file: any) { if (file.web_url) window.open(file.web_url, '_blank') }
async function toggleFav(file: any) {
  await toggleFileFavorite(file.id)
  file.is_favorite = !file.is_favorite
}

async function handleAddSource() {
  if (!sourceForm.name) return
  await createDocumentSource({ ...sourceForm })
  ElMessage.success('文档源已添加')
  showAddSource.value = false
  sourceForm.name = ''; sourceForm.url = ''; sourceForm.site_id = ''; sourceForm.drive_id = ''; sourceForm.folder_path = ''
  fetchSources()
}

onMounted(fetchSources)
</script>

<style scoped>
.doc-center { max-width: 1100px; margin: 0 auto; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.page-header h2 { display: flex; align-items: center; gap: 8px; font-size: 22px; font-weight: 800; }
.sources-row { display: flex; gap: 8px; flex-wrap: wrap; }
.source-tab { display: flex; align-items: center; gap: 6px; padding: 10px 16px; border-radius: 10px; cursor: pointer; font-size: 14px; font-weight: 500; border: 1px solid var(--border-color); transition: all var(--transition); }
.source-tab.active, .source-tab:hover { background: var(--accent); color: white; border-color: var(--accent); }
.files-header { display: flex; align-items: center; gap: 12px; padding: 12px 16px; margin-bottom: 12px; }
.file-list { display: flex; flex-direction: column; gap: 4px; }
.file-item { display: flex; align-items: center; gap: 12px; padding: 12px 16px; cursor: pointer; }
.file-info { flex: 1; min-width: 0; }
.file-name { font-size: 14px; font-weight: 500; display: block; }
.file-meta { font-size: 11px; color: var(--text-muted); }
</style>
