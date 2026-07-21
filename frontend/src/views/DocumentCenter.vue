<template>
  <div class="doc-center">
    <div class="page-header">
      <h2><el-icon><Files /></el-icon> 文档中心</h2>
      <el-button v-if="!authStore.isGuest()" type="primary" @click="showAddSource = true">
        <el-icon><Plus /></el-icon> 添加文档源
      </el-button>
    </div>

    <!-- Sources -->
    <div class="sources-row mb-4">
      <div v-for="src in sources" :key="src.id"
        :class="['source-tab', { active: selectedSource === src.id }]"
        @click="selectSource(src)">
        <el-icon><component :is="sourceIcon(src.source_type)" /></el-icon>
        <span>{{ src.name }}</span>
        <el-tag size="small">{{ src.source_type }}</el-tag>
        <el-button v-if="!authStore.isGuest()" text size="small" class="src-del" @click.stop="deleteSource(src)">
          <el-icon><Close /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- Local Folder Browser -->
    <div v-if="selectedSource && currentSource?.source_type === 'local'" class="local-browser">
      <div class="files-header glass">
        <div class="header-left">
          <el-button :disabled="!breadcrumbs.length" text @click="goToParent">
            <el-icon size="18"><ArrowLeft /></el-icon>
          </el-button>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item v-for="(b, i) in breadcrumbs" :key="i">
              <span class="crumb-link" @click="goToBreadcrumb(i)">{{ b.name }}</span>
            </el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentFolderName }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-input v-model="localSearch" placeholder="模糊搜索文件/文件夹..." style="width:260px" size="default" clearable
            @keyup.enter="doLocalSearch" @clear="clearSearch">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
        </div>
      </div>

      <div v-loading="treeLoading">
        <template v-if="isSearching">
          <div class="search-stats glass" v-if="searchResults.length">找到 {{ searchResults.length }} 个结果</div>
          <div v-if="searchResults.length" class="file-list">
            <div v-for="item in searchResults" :key="item.path" class="file-item glass glass-hover" @click="openSearchResult(item)">
              <el-icon size="20" :color="item.type === 'group' ? '#fdcb6e' : 'var(--text-muted)'">
                <Folder v-if="item.type === 'group'" /><Document v-else />
              </el-icon>
              <div class="file-info">
                <span class="file-name">{{ item.name }}</span>
                <span class="file-meta">{{ item.type === 'file' ? formatSize(item.size) : '文件夹' }} · {{ formatDate(item.modified) }}</span>
              </div>
            </div>
          </div>
          <el-empty v-else description="未找到匹配结果" />
        </template>

        <template v-else>
          <div v-if="treeData.groups.length" class="tree-groups">
            <div v-for="g in treeData.groups" :key="g.path" class="tree-group glass">
              <div class="group-header" @click="enterGroup(g)">
                <el-icon color="#fdcb6e" size="18"><Folder /></el-icon>
                <span class="group-name">{{ g.name }}</span>
                <span class="group-count">{{ g.children_count }} 项</span>
                <el-icon class="group-arrow"><ArrowRight /></el-icon>
              </div>
            </div>
          </div>

          <div v-if="treeData.files.length" class="file-list">
            <div v-for="f in treeData.files" :key="f.path" class="file-item glass glass-hover" @click="openFile(f)">
              <el-icon size="20" :color="fileIconColor(f.name)">
                <Document />
              </el-icon>
              <div class="file-info">
                <span class="file-name">{{ f.name }}</span>
                <span class="file-meta">{{ formatSize(f.size) }} · {{ formatDate(f.modified) }}</span>
              </div>
              <div class="file-actions" @click.stop>
                <el-button text size="small" @click="openFile(f)"><el-icon><View /></el-icon></el-button>
                <el-button text size="small" @click="downloadFile(f)"><el-icon><Download /></el-icon></el-button>
              </div>
            </div>
          </div>
          <el-empty v-if="!treeData.groups.length && !treeData.files.length && !treeLoading" description="空文件夹" />
        </template>
      </div>
    </div>

    <!-- Non-local placeholder -->
    <div v-else-if="selectedSource && currentSource?.source_type !== 'local'" class="placeholder-card glass">
      <el-icon size="40"><Connection /></el-icon>
      <p>{{ currentSource?.source_type }} 源需配置云服务凭据</p>
      <p class="text-secondary">请在系统设置中配置 OAuth</p>
    </div>

    <div v-else-if="!selectedSource" class="placeholder-card glass">
      <el-icon size="40"><FolderOpened /></el-icon>
      <p>选择上方文档源开始浏览</p>
      <p class="text-secondary">
        <template v-if="authStore.isGuest()">访客模式：仅可浏览文档</template>
        <template v-else>点击"添加文档源"配置本地文件夹</template>
      </p>
    </div>

    <!-- Preview Dialog -->
    <el-dialog v-model="showPreview" :title="previewFile?.name || '文件预览'" width="80%" top="3vh" destroy-on-close>
      <div v-if="previewFile" class="preview-container">
        <template v-if="isPreviewableImage(previewFile)">
          <img :src="filePreviewUrl" style="max-width:100%;max-height:70vh;display:block;margin:0 auto" />
        </template>
        <template v-else-if="isPreviewableText(previewFile)">
          <pre class="text-preview">{{ previewContent }}</pre>
        </template>
        <template v-else-if="isPreviewablePdf(previewFile)">
          <iframe :src="filePreviewUrl" style="width:100%;height:70vh;border:none" />
        </template>
        <template v-else>
          <div class="no-preview">
            <el-icon size="48"><Document /></el-icon>
            <p>此文件类型不支持在线预览</p>
            <el-button type="primary" @click="downloadFile(previewFile!)"><el-icon><Download /></el-icon> 下载文件</el-button>
          </div>
        </template>
      </div>
    </el-dialog>

    <!-- Add Source Dialog -->
    <el-dialog v-model="showAddSource" title="添加文档源" width="520px">
      <el-form :model="sourceForm" label-position="top">
        <el-form-item label="名称 *"><el-input v-model="sourceForm.name" placeholder="如: 5G 文档库" /></el-form-item>
        <el-form-item label="类型">
          <el-select v-model="sourceForm.source_type" style="width:100%">
            <el-option value="local" label="本地文件夹" />
            <el-option value="sharepoint" label="SharePoint" />
            <el-option value="onedrive" label="OneDrive" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="sourceForm.source_type === 'local'" label="文件夹路径 *">
          <el-input v-model="sourceForm.folder_path" placeholder="Docker: /app/docs  本机: C:\Users\..." />
          <div class="form-hint">Docker 部署时需在 compose 中添加: - /你的本地路径:/app/docs:ro</div>
        </el-form-item>
        <el-form-item v-else label="URL"><el-input v-model="sourceForm.url" placeholder="https://..." /></el-form-item>
      </el-form>
      <template #footer><el-button @click="showAddSource = false">取消</el-button><el-button type="primary" @click="handleAddSource">添加</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { getDocumentSources, createDocumentSource, deleteDocumentSource, browseLocalFolder, getLocalFileUrl, searchLocalFolder } from '../api'
import { useAuthStore } from '../stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'

const authStore = useAuthStore()
const sources = ref<any[]>([])
const selectedSource = ref<number | null>(null)
const currentPath = ref('')
const treeData = ref<{ groups: any[]; files: any[] }>({ groups: [], files: [] })
const treeLoading = ref(false)
const localSearch = ref('')
const searchResults = ref<any[]>([])
const isSearching = ref(false)
const showAddSource = ref(false)
const showPreview = ref(false)
const previewFile = ref<any>(null)
const previewContent = ref('')
const sourceForm = reactive({ name: '', source_type: 'local', url: '', site_id: '', drive_id: '', folder_path: '' })

const currentSource = computed(() => sources.value.find(s => s.id === selectedSource.value))
const currentFolderName = computed(() => currentPath.value.split('/').pop() || currentSource.value?.name || '')
const breadcrumbs = computed(() => {
  if (!currentPath.value) return []
  const parts = currentPath.value.split('/')
  return parts.slice(0, -1).map((p, i) => ({ name: p, path: parts.slice(0, i + 1).join('/') }))
})
const filePreviewUrl = computed(() => {
  if (!previewFile.value || !selectedSource.value) return ''
  return getLocalFileUrl(selectedSource.value, previewFile.value.path)
})

function sourceIcon(type: string) { const m: Record<string,string>={local:'FolderOpened',sharepoint:'Platform',onedrive:'FolderOpened',custom:'Folder'}; return m[type]||'Folder' }
function fileIconColor(name: string) {
  const ext = (name||'').split('.').pop()?.toLowerCase()||''
  const m: Record<string,string>={xlsx:'#00b894',xls:'#00b894',csv:'#00b894',docx:'#0984e3',doc:'#0984e3',pptx:'#e17055',ppt:'#e17055',pdf:'#d63031',txt:'#636e72',md:'#6c5ce7',py:'#0984e3',js:'#fdcb6e',ts:'#0984e3',json:'#fdcb6e',xml:'#e17055',html:'#e17055',css:'#0984e3',zip:'#636e72',png:'#00b894',jpg:'#00b894',jpeg:'#00b894',gif:'#00b894',svg:'#00b894',mp4:'#d63031',mp3:'#e17055'}
  return m[ext]||'var(--text-muted)'
}
function formatSize(b: number) { if (!b) return '0B'; return b<1024*1024?Math.round(b/1024)+'KB':(b/(1024*1024)).toFixed(1)+'MB' }
function formatDate(d: string|null) { if (!d) return ''; try{return new Date(d).toLocaleDateString('zh-CN')}catch{return ''} }
function isPreviewableImage(f: any) { return /^image\//.test(f.mime||'') }
function isPreviewableText(f: any) { return /^(text\/|application\/json|application\/xml)/.test(f.mime||'') }
function isPreviewablePdf(f: any) { return (f.mime||'')==='application/pdf' }

async function fetchSources() { const { data } = await getDocumentSources(); sources.value = data }

async function selectSource(src: any) {
  selectedSource.value = src.id; currentPath.value = ''; isSearching.value = false; localSearch.value = ''; searchResults.value = []
  if (src.source_type === 'local') await browseFolder('')
}

async function browseFolder(path: string) {
  if (!selectedSource.value) return
  treeLoading.value = true
  try { const { data } = await browseLocalFolder(selectedSource.value, path); treeData.value = data; currentPath.value = path }
  catch (e: any) { ElMessage.error(e?.response?.data?.detail||'浏览失败'); treeData.value = { groups:[], files:[] } }
  treeLoading.value = false
}

function enterGroup(g: any) { browseFolder(g.path) }
function goToParent() { const parts = currentPath.value.split('/'); parts.pop(); browseFolder(parts.join('/')) }
function goToBreadcrumb(index: number) { const parts = currentPath.value.split('/'); browseFolder(parts.slice(0, index + 1).join('/')) }

function openFile(f: any) {
  previewFile.value = f
  if (isPreviewableText(f)) {
    fetch(getLocalFileUrl(selectedSource.value!, f.path))
      .then(r => r.text()).then(t => { previewContent.value = t; showPreview.value = true })
      .catch(() => { showPreview.value = true })
  } else { showPreview.value = true }
}

function downloadFile(f: any) {
  const a = document.createElement('a'); a.href = getLocalFileUrl(selectedSource.value!, f.path, true); a.download = f.name; a.click()
}

async function doLocalSearch() {
  if (!localSearch.value.trim() || !selectedSource.value) return
  isSearching.value = true; treeLoading.value = true
  try { const { data } = await searchLocalFolder(selectedSource.value, localSearch.value.trim()); searchResults.value = data.results || [] }
  catch { searchResults.value = [] }
  treeLoading.value = false
}

function clearSearch() { isSearching.value = false; searchResults.value = [] }

function openSearchResult(item: any) {
  if (item.type === 'group') { browseFolder(item.path); isSearching.value = false; localSearch.value = '' }
  else openFile(item)
}

async function handleAddSource() {
  if (!sourceForm.name) return
  await createDocumentSource({ ...sourceForm })
  ElMessage.success('文档源已添加'); showAddSource.value = false
  sourceForm.name = ''; sourceForm.url = ''; sourceForm.folder_path = ''; fetchSources()
}

async function deleteSource(src: any) {
  try { await ElMessageBox.confirm(`删除 "${src.name}"？`, '确认', { type:'warning' }); await deleteDocumentSource(src.id); if (selectedSource.value===src.id) selectedSource.value=null; ElMessage.success('已删除'); fetchSources() }
  catch { /* */ }
}

onMounted(fetchSources)
</script>

<style scoped>
.doc-center { max-width: 1200px; margin: 0 auto; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.page-header h2 { display: flex; align-items: center; gap: 8px; font-size: 22px; font-weight: 800; }
.sources-row { display: flex; gap: 8px; flex-wrap: wrap; }
.source-tab { display: flex; align-items: center; gap: 6px; padding: 10px 16px; border-radius: 10px; cursor: pointer; font-size: 14px; font-weight: 500; border: 1px solid var(--border-color); transition: all var(--transition); position: relative; }
.source-tab.active, .source-tab:hover { background: var(--accent); color: white; border-color: var(--accent); }
.source-tab.active .src-del { color: rgba(255,255,255,0.7); }
.src-del { opacity: 0; transition: opacity 0.2s; }
.source-tab:hover .src-del { opacity: 1; }
.files-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 12px 16px; margin-bottom: 12px; flex-wrap: wrap; }
.header-left { display: flex; align-items: center; gap: 8px; }
.crumb-link { cursor: pointer; color: var(--accent); }
.crumb-link:hover { text-decoration: underline; }
.search-stats { padding: 10px 16px; margin-bottom: 8px; font-size: 13px; color: var(--text-secondary); }
.tree-groups { display: flex; flex-direction: column; gap: 4px; margin-bottom: 8px; }
.group-header { display: flex; align-items: center; gap: 10px; padding: 14px 18px; cursor: pointer; transition: background 0.2s; }
.group-header:hover { background: var(--bg-primary); }
.group-name { flex: 1; font-size: 15px; font-weight: 600; }
.group-count { font-size: 12px; color: var(--text-muted); }
.group-arrow { color: var(--text-muted); transition: transform 0.2s; }
.group-header:hover .group-arrow { transform: translateX(4px); }
.file-list { display: flex; flex-direction: column; gap: 2px; }
.file-item { display: flex; align-items: center; gap: 12px; padding: 12px 16px; cursor: pointer; }
.file-info { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 3px; }
.file-name { font-size: 14px; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.file-meta { font-size: 11px; color: var(--text-muted); }
.file-actions { display: flex; gap: 2px; opacity: 0; transition: opacity 0.2s; }
.file-item:hover .file-actions { opacity: 1; }
.placeholder-card { padding: 48px; text-align: center; }
.placeholder-card p { margin: 12px 0 4px; font-size: 15px; }
.text-secondary { color: var(--text-secondary); font-size: 13px; }
.form-hint { margin-top: 4px; font-size: 12px; color: var(--text-muted); line-height: 1.5; }
.text-preview { max-height: 70vh; overflow: auto; white-space: pre-wrap; font-family: monospace; font-size: 13px; padding: 16px; background: var(--bg-primary); border-radius: 8px; }
.no-preview { text-align: center; padding: 40px; }
.no-preview p { margin: 16px 0; color: var(--text-secondary); }
@media (max-width: 768px) { .files-header { flex-direction: column; align-items: stretch; } }
</style>
