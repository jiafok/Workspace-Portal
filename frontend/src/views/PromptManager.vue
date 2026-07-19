<template>
  <div class="prompt-manager">
    <div class="page-header">
      <h2><el-icon><Document /></el-icon> Prompt 管理中心</h2>
      <div class="header-actions">
        <el-button @click="doExport"><el-icon><Download /></el-icon> 导出</el-button>
        <el-upload :auto-upload="false" :show-file-list="false" accept=".json" :on-change="doImport">
          <el-button><el-icon><Upload /></el-icon> 导入</el-button>
        </el-upload>
        <el-button type="primary" @click="openCreate"><el-icon><Plus /></el-icon> 新建 Prompt</el-button>
      </div>
    </div>

    <!-- Filters -->
    <div class="filters glass mb-4">
      <el-radio-group v-model="filterCategory" size="small" @change="fetchPrompts">
        <el-radio-button value="">全部</el-radio-button>
        <el-radio-button v-for="c in categories" :key="c" :value="c">{{ c }}</el-radio-button>
      </el-radio-group>
      <el-input v-model="searchText" placeholder="搜索 Prompt..." class="filter-search" clearable />
    </div>

    <!-- Prompt List -->
    <div v-loading="loading">
      <div v-for="prompt in filteredList" :key="prompt.id" class="prompt-card glass glass-hover">
        <div class="prompt-top">
          <div class="prompt-info">
            <h4>{{ prompt.title }}</h4>
            <div class="prompt-meta">
              <el-tag size="small">{{ prompt.category }}</el-tag>
              <span class="text-xs text-muted">v{{ prompt.version }}</span>
              <span class="text-xs text-muted">使用 {{ prompt.use_count }} 次</span>
            </div>
          </div>
          <div class="prompt-actions">
            <el-button size="small" @click="usePrompt(prompt)"><el-icon><Promotion /></el-icon> 使用</el-button>
            <el-button size="small" @click="copyContent(prompt)"><el-icon><CopyDocument /></el-icon></el-button>
            <el-button size="small" @click="openEdit(prompt)"><el-icon><Edit /></el-icon></el-button>
            <el-button size="small" type="danger" @click="handleDelete(prompt)"><el-icon><Delete /></el-icon></el-button>
          </div>
        </div>
        <div class="prompt-preview" @click="expandedId = expandedId === prompt.id ? null : prompt.id">
          <pre>{{ prompt.content.slice(0, expandedId === prompt.id ? prompt.content.length : 200) }}</pre>
          <span v-if="prompt.content.length > 200 && expandedId !== prompt.id" class="expand-hint">点击展开全部...</span>
        </div>
      </div>
      <el-empty v-if="!loading && !filteredList.length" description="暂无 Prompt，点击新建按钮创建" />
    </div>

    <!-- Create/Edit Dialog -->
    <el-dialog v-model="showDialog" :title="editing ? '编辑 Prompt' : '新建 Prompt'" width="620px">
      <el-form :model="form" label-position="top">
        <el-form-item label="标题 *">
          <el-input v-model="form.title" placeholder="如: 客户邮件回复模板" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="form.category" style="width:100%" filterable allow-create>
            <el-option v-for="c in categories" :key="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="内容 *">
          <el-input v-model="form.content" type="textarea" :rows="8" placeholder="输入 Prompt 内容...&#10;使用 {{变量}} 标记可变部分" />
        </el-form-item>
        <el-form-item label="标签">
          <el-input v-model="form.tags" placeholder="逗号分隔, 如: 邮件,客户,技术支持" />
        </el-form-item>
        <el-form-item label="公开">
          <el-switch v-model="form.is_public" />
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
import { getPrompts, createPrompt, updatePrompt, deletePrompt, recordPromptUse, getPromptCategories, exportPrompts, importPrompts } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const prompts = ref<any[]>([])
const categories = ref<string[]>([])
const loading = ref(false)
const filterCategory = ref('')
const searchText = ref('')
const expandedId = ref<number | null>(null)
const showDialog = ref(false)
const editing = ref<any>(null)
const form = reactive({ title: '', content: '', category: '通用', tags: '', is_public: false })

const filteredList = computed(() => {
  let list = prompts.value
  if (filterCategory.value) list = list.filter(p => p.category === filterCategory.value)
  if (searchText.value) {
    const q = searchText.value.toLowerCase()
    list = list.filter(p => p.title.toLowerCase().includes(q) || p.content.toLowerCase().includes(q) || p.tags.toLowerCase().includes(q))
  }
  return list
})

async function fetchPrompts() {
  loading.value = true
  try {
    const { data } = await getPrompts({ category: filterCategory.value || undefined })
    prompts.value = data
  } catch { /* */ }
  loading.value = false
}

function openCreate() {
  editing.value = null
  form.title = ''; form.content = ''; form.category = '通用'; form.tags = ''; form.is_public = false
  showDialog.value = true
}

function openEdit(p: any) {
  editing.value = p
  form.title = p.title; form.content = p.content; form.category = p.category; form.tags = p.tags; form.is_public = p.is_public
  showDialog.value = true
}

async function handleSave() {
  if (!form.title || !form.content) return
  if (editing.value) {
    await updatePrompt(editing.value.id, { ...form })
    ElMessage.success('已更新 (新版本已创建)')
  } else {
    await createPrompt({ ...form })
    ElMessage.success('已创建')
  }
  showDialog.value = false
  await fetchPrompts()
}

async function handleDelete(p: any) {
  try {
    await ElMessageBox.confirm(`删除 "${p.title}"？`, '确认', { type: 'warning' })
    await deletePrompt(p.id); ElMessage.success('已删除'); fetchPrompts()
  } catch { /* */ }
}

async function usePrompt(p: any) {
  await recordPromptUse(p.id)
  // Navigate to AI chat with this prompt
  localStorage.setItem('wp_current_prompt', p.content)
  window.open('/ai-chat', '_blank')
}

function copyContent(p: any) {
  navigator.clipboard.writeText(p.content); ElMessage.success('已复制到剪贴板')
}

async function doExport() {
  try {
    const { data } = await exportPrompts()
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = 'prompts_export.json'; a.click()
    URL.revokeObjectURL(url); ElMessage.success('导出成功')
  } catch { ElMessage.error('导出失败') }
}

async function doImport(file: any) {
  try {
    const text = await file.raw.text()
    const data = JSON.parse(text)
    await importPrompts(data)
    ElMessage.success('导入成功')
    fetchPrompts()
  } catch { ElMessage.error('导入失败，请检查格式') }
}

onMounted(async () => {
  try {
    const { data } = await getPromptCategories()
    categories.value = data.categories
  } catch { categories.value = [] }
  fetchPrompts()
})
</script>

<style scoped>
.prompt-manager { max-width: 1100px; margin: 0 auto; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.page-header h2 { display: flex; align-items: center; gap: 8px; font-size: 22px; font-weight: 800; }
.header-actions { display: flex; gap: 8px; }
.filters { padding: 12px 16px; display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.filter-search { width: 200px; }
.prompt-card { padding: 16px 20px; margin-bottom: 10px; }
.prompt-top { display: flex; align-items: flex-start; justify-content: space-between; }
.prompt-info h4 { font-size: 16px; font-weight: 700; margin-bottom: 6px; }
.prompt-meta { display: flex; gap: 8px; align-items: center; }
.prompt-actions { display: flex; gap: 4px; opacity: 0; transition: opacity 0.2s; }
.prompt-card:hover .prompt-actions { opacity: 1; }
.prompt-preview { margin-top: 12px; cursor: pointer; }
.prompt-preview pre { background: var(--bg-primary); padding: 12px; border-radius: 8px; font-size: 13px; white-space: pre-wrap; word-break: break-word; max-height: 120px; overflow: hidden; }
.expand-hint { font-size: 12px; color: var(--accent); display: block; margin-top: 4px; text-align: center; }
@media (max-width: 768px) { .prompt-actions { opacity: 1; } }
</style>
