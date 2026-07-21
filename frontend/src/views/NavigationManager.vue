<template>
  <div class="nav-manager">
    <!-- Toolbar -->
    <div class="toolbar glass">
      <div class="toolbar-left">
        <el-button v-if="!authStore.isGuest()" type="primary" @click="showAddCategory = true">
          <el-icon><FolderAdd /></el-icon> 新增分类
        </el-button>
        <el-button v-if="!authStore.isGuest()" @click="openBulkEditor">
          <el-icon><EditPen /></el-icon> 批量编辑
        </el-button>
        <el-button v-if="!authStore.isGuest()" @click="showImport = true">
          <el-icon><Upload /></el-icon> 导入收藏夹
        </el-button>
      </div>
      <div class="toolbar-right">
        <el-input
          v-model="searchText"
          placeholder="搜索网站..."
          clearable
          size="default"
          style="width: 220px"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
      </div>
    </div>

    <!-- Categories -->
    <div v-loading="navigationStore.loading">
      <div v-for="(category, index) in sortedCategories" :key="category.id" class="category-section animate-in">
        <CategoryPanel
          :category="category"
          :websites="getFilteredWebsites(category.id)"
          :index="index"
          @add-website="(cat) => openAddWebsite(cat)"
          @edit-category="(cat) => { editingCategory = cat; editCategoryForm.name = cat.name; editCategoryForm.icon = cat.icon; showEditCategory = true }"
          @delete-category="handleDeleteCategory"
          @edit-website="openEditWebsite"
          @delete-website="handleDeleteWebsite"
          @refresh="refreshData"
        />
      </div>

      <el-empty v-if="!navigationStore.categories.length" description="暂无分类，点击上方按钮添加" />
    </div>

    <!-- Add Category Dialog -->
    <el-dialog v-model="showAddCategory" title="新增分类" width="420px">
      <el-form :model="categoryForm" label-position="top">
        <el-form-item label="分类名称">
          <el-input v-model="categoryForm.name" placeholder="如: 常用工具" />
        </el-form-item>
        <el-form-item label="图标">
          <el-select v-model="categoryForm.icon" placeholder="选择图标">
            <el-option v-for="ic in iconList" :key="ic" :value="ic" :label="ic">
              <el-icon style="margin-right:8px"><component :is="ic" /></el-icon>{{ ic }}
            </el-option>
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddCategory = false">取消</el-button>
        <el-button type="primary" @click="handleAddCategory">确认</el-button>
      </template>
    </el-dialog>

    <!-- Edit Category Dialog -->
    <el-dialog v-model="showEditCategory" title="编辑分类" width="420px">
      <el-form :model="editCategoryForm" label-position="top">
        <el-form-item label="分类名称">
          <el-input v-model="editCategoryForm.name" />
        </el-form-item>
        <el-form-item label="图标">
          <el-select v-model="editCategoryForm.icon">
            <el-option v-for="ic in iconList" :key="ic" :value="ic" :label="ic" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditCategory = false">取消</el-button>
        <el-button type="primary" @click="handleEditCategory">保存</el-button>
      </template>
    </el-dialog>

    <!-- Add/Edit Website Dialog -->
    <el-dialog v-model="showWebsiteDialog" :title="editingWebsite ? '编辑网站' : '新增网站'" width="520px">
      <el-form :model="websiteForm" label-position="top">
        <el-form-item label="网站名称">
          <el-input v-model="websiteForm.name" placeholder="留空则自动获取" />
        </el-form-item>
        <el-form-item label="网址 *">
          <el-input v-model="websiteForm.url" placeholder="https://example.com" />
        </el-form-item>
        <el-form-item label="图标URL">
          <el-input v-model="websiteForm.icon_url" placeholder="留空则自动获取 favicon" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="websiteForm.description" type="textarea" :rows="2" placeholder="留空则自动获取" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="websiteForm.notes" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="websiteForm.category_id" style="width:100%">
            <el-option v-for="c in navigationStore.categories" :key="c.id" :value="c.id" :label="c.name" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showWebsiteDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSaveWebsite">
          {{ editingWebsite ? '保存' : '新增并自动获取信息' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- Import Dialog -->
    <el-dialog v-model="showImport" title="导入收藏夹" width="560px">
      <BookmarkImport @done="onImportDone" />
    </el-dialog>

    <el-dialog v-model="showBulkEditor" title="批量编辑导航" width="860px" top="5vh">
      <div class="bulk-tip">
        适合大量 NAS / 导航条目统一维护。可直接修改分类、排序和网站字段；本次保存会新增或更新现有条目，不会自动删除未出现在 JSON 里的旧条目。
      </div>
      <el-input
        v-model="bulkEditorText"
        type="textarea"
        :rows="22"
        placeholder="[{ name, icon, sort_order, websites: [...] }]"
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
import { useNavigationStore } from '../stores/navigation'
import { useAuthStore } from '../stores/auth'
import CategoryPanel from '../components/CategoryPanel.vue'
import BookmarkImport from '../components/BookmarkImport.vue'
import draggable from 'vuedraggable'
import { ElMessage, ElMessageBox } from 'element-plus'

const navigationStore = useNavigationStore()
const authStore = useAuthStore()

const searchText = ref('')
const showAddCategory = ref(false)
const showEditCategory = ref(false)
const showWebsiteDialog = ref(false)
const editingWebsite = ref<any>(null)
const editingCategory = ref<any>(null)
const showImport = ref(false)
const showBulkEditor = ref(false)
const bulkEditorText = ref('')
const bulkSaving = ref(false)

const categoryForm = reactive({ name: '', icon: 'Folder' })
const editCategoryForm = reactive({ name: '', icon: '' })
const websiteForm = reactive({
  name: '', url: '', icon_url: '', description: '', category_id: 0, notes: ''
})

const iconList = ['Folder', 'Cpu', 'OfficeBuilding', 'Monitor', 'Document', 'Service', 'FolderOpened', 'Connection', 'Star', 'MagicStick', 'Tools', 'DataAnalysis', 'Notebook', 'Platform', 'Guide']

const sortedCategories = computed({
  get: () => [...navigationStore.categories].sort((a, b) => a.sort_order - b.sort_order),
  set: () => {},
})

function getFilteredWebsites(catId: number) {
  const sites = (navigationStore.websitesByCategory[catId] || []).sort((a, b) => a.sort_order - b.sort_order)
  if (!searchText.value) return sites
  const q = searchText.value.toLowerCase()
  return sites.filter(w => w.name.toLowerCase().includes(q) || w.url.toLowerCase().includes(q))
}

function openAddWebsite(cat: any) {
  editingWebsite.value = null
  websiteForm.name = ''
  websiteForm.url = ''
  websiteForm.icon_url = ''
  websiteForm.description = ''
  websiteForm.notes = ''
  websiteForm.category_id = cat.id
  showWebsiteDialog.value = true
}

function openEditWebsite(website: any) {
  editingWebsite.value = website
  websiteForm.name = website.name || ''
  websiteForm.url = website.url || ''
  websiteForm.icon_url = website.icon_url || ''
  websiteForm.description = website.description || ''
  websiteForm.notes = website.notes || ''
  websiteForm.category_id = website.category_id
  showWebsiteDialog.value = true
}

async function handleAddCategory() {
  if (!categoryForm.name.trim()) return
  await navigationStore.addCategory({ name: categoryForm.name.trim(), icon: categoryForm.icon })
  ElMessage.success('分类已添加')
  showAddCategory.value = false
  categoryForm.name = ''
}

async function handleEditCategory() {
  if (!editingCategory.value) return
  await navigationStore.editCategory(editingCategory.value.id, {
    name: editCategoryForm.name, icon: editCategoryForm.icon
  })
  ElMessage.success('分类已更新')
  showEditCategory.value = false
}

async function handleSaveWebsite() {
  if (!websiteForm.url.trim()) return
  const data = { ...websiteForm }
  if (editingWebsite.value) {
    await navigationStore.editWebsite(editingWebsite.value.id, data)
    ElMessage.success('网站已更新')
  } else {
    await navigationStore.addWebsite(data)
    ElMessage.success('网站已添加')
  }
  showWebsiteDialog.value = false
}

async function handleDeleteWebsite(website: any) {
  try {
    await ElMessageBox.confirm(`确定删除网站 "${website.name}"？`, '确认删除', { type: 'warning' })
    await navigationStore.removeWebsite(website.id)
    ElMessage.success('网站已删除')
  } catch { /* cancelled */ }
}

async function onCategoryDragChange() {
  const items = sortedCategories.value.map((c, i) => ({ id: c.id, sort_order: i }))
  await navigationStore.reorderCategories(items)
}

async function refreshData() {
  await navigationStore.fetchAll()
}

async function handleDeleteCategory(cat: any) {
  try {
    await ElMessageBox.confirm(`确定删除分类 "${cat.name}" 及其所有网站？`, '确认删除', { type: 'warning' })
    await navigationStore.removeCategory(cat.id)
    ElMessage.success('分类已删除')
  } catch { /* cancelled */ }
}

function onImportDone() {
  setTimeout(() => {
    showImport.value = false
    refreshData()
    ElMessage.success('收藏夹导入完成')
  }, 1500)
}

function openBulkEditor() {
  bulkEditorText.value = JSON.stringify(
    sortedCategories.value.map((category, index) => ({
      id: category.id,
      name: category.name,
      icon: category.icon,
      sort_order: index,
      websites: getFilteredWebsites(category.id).map((website, siteIndex) => ({
        id: website.id,
        name: website.name,
        url: website.url,
        icon_url: website.icon_url,
        description: website.description,
        notes: website.notes,
        is_pinned: website.is_pinned,
        is_favorite: website.is_favorite,
        sort_order: siteIndex,
      })),
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
    const categoryNameToId = new Map<string, number>()
    const existingCategories = new Map(navigationStore.categories.map((category) => [category.id, category]))

    for (let categoryIndex = 0; categoryIndex < parsed.length; categoryIndex += 1) {
      const category = parsed[categoryIndex]
      const payload = {
        name: String(category.name || '').trim(),
        icon: String(category.icon || 'Folder').trim() || 'Folder',
        sort_order: Number.isFinite(Number(category.sort_order)) ? Number(category.sort_order) : categoryIndex,
      }
      if (!payload.name) continue

      let categoryId = Number(category.id)
      if (existingCategories.has(categoryId)) {
        await navigationStore.editCategory(categoryId, payload)
      } else {
        const created = await navigationStore.addCategory({ name: payload.name, icon: payload.icon })
        categoryId = created.id
        await navigationStore.editCategory(categoryId, { sort_order: payload.sort_order })
      }
      categoryNameToId.set(payload.name, categoryId)

      const websites = Array.isArray(category.websites) ? category.websites : []
      for (let siteIndex = 0; siteIndex < websites.length; siteIndex += 1) {
        const website = websites[siteIndex]
        const sitePayload = {
          name: String(website.name || '').trim(),
          url: String(website.url || '').trim(),
          icon_url: String(website.icon_url || ''),
          description: String(website.description || ''),
          notes: String(website.notes || ''),
          category_id: categoryId,
          is_pinned: Boolean(website.is_pinned),
          is_favorite: Boolean(website.is_favorite),
          sort_order: Number.isFinite(Number(website.sort_order)) ? Number(website.sort_order) : siteIndex,
        }
        if (!sitePayload.url) continue

        const websiteId = Number(website.id)
        if (navigationStore.websites.some((item) => item.id === websiteId)) {
          await navigationStore.editWebsite(websiteId, sitePayload)
        } else {
          await navigationStore.addWebsite(sitePayload)
        }
      }
    }

    await refreshData()
    showBulkEditor.value = false
    ElMessage.success('批量修改已保存')
  } catch {
    ElMessage.error('批量保存失败，请检查字段内容')
  } finally {
    bulkSaving.value = false
  }
}

onMounted(() => {
  navigationStore.fetchAll()
})
</script>

<style scoped>
.nav-manager {
  max-width: 1300px;
  margin: 0 auto;
}
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  margin-bottom: 20px;
  position: sticky;
  top: 80px;
  z-index: 40;
}
.toolbar-left, .toolbar-right {
  display: flex;
  gap: 8px;
  align-items: center;
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
.category-section {
  margin-bottom: 4px;
}
.category-header-row {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}
.cat-drag-handle {
  cursor: grab;
  padding: 16px 4px 0;
  color: var(--text-muted);
  flex-shrink: 0;
}
.cat-drag-handle:active {
  cursor: grabbing;
}

@media (max-width: 768px) {
  .toolbar {
    flex-direction: column;
    gap: 10px;
    top: 100px;
  }
  .toolbar-right {
    width: 100%;
  }
  .toolbar-right .el-input {
    width: 100% !important;
  }
}
</style>
