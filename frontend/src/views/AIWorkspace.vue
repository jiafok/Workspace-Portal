<template>
  <div class="ai-workspace">
    <div class="page-header">
      <h2><el-icon><MagicStick /></el-icon> AI 工作区</h2>
      <el-button type="primary" @click="showAdd = true">
        <el-icon><Plus /></el-icon> 添加 AI
      </el-button>
    </div>

    <!-- Pinned -->
    <div v-if="pinnedProviders.length" class="section">
      <h3 class="section-label">📌 已置顶</h3>
      <div class="ai-grid">
        <div v-for="ai in pinnedProviders" :key="ai.id" class="ai-card glass glass-hover" @click="openAI(ai)">
          <div class="ai-icon">{{ ai.name[0] }}</div>
          <span class="ai-name">{{ ai.name }}</span>
          <div class="ai-actions">
            <el-button text size="small" @click.stop="togglePin(ai)"><el-icon><Top /></el-icon></el-button>
            <el-button text size="small" @click.stop="openEdit(ai)"><el-icon><Edit /></el-icon></el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- Favorites -->
    <div v-if="favoriteProviders.length" class="section">
      <h3 class="section-label">⭐ 收藏</h3>
      <div class="ai-grid">
        <div v-for="ai in favoriteProviders" :key="ai.id" class="ai-card glass glass-hover" @click="openAI(ai)">
          <div class="ai-icon">{{ ai.name[0] }}</div>
          <span class="ai-name">{{ ai.name }}</span>
          <div class="ai-actions">
            <el-button text size="small" @click.stop="toggleFavorite(ai)"><el-icon><StarFilled /></el-icon></el-button>
            <el-button text size="small" @click.stop="togglePin(ai)"><el-icon><Top /></el-icon></el-button>
            <el-button text size="small" @click.stop="openEdit(ai)"><el-icon><Edit /></el-icon></el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- All enabled -->
    <div class="section">
      <h3 class="section-label">🤖 全部 AI</h3>
      <div class="ai-grid">
        <div v-for="ai in sortedProviders" :key="ai.id" class="ai-card glass glass-hover" @click="openAI(ai)">
          <div class="ai-icon">{{ ai.name[0] }}</div>
          <span class="ai-name">{{ ai.name }}</span>
          <div class="ai-actions">
            <el-button text size="small" @click.stop="toggleFavorite(ai)">
              <el-icon><Star /></el-icon>
            </el-button>
            <el-button text size="small" @click.stop="togglePin(ai)">
              <el-icon><Top /></el-icon>
            </el-button>
            <el-button text size="small" @click.stop="openEdit(ai)">
              <el-icon><Edit /></el-icon>
            </el-button>
            <el-button text size="small" @click.stop="handleDelete(ai)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- Recent -->
    <div v-if="recentProviders.length" class="section">
      <h3 class="section-label">🕐 最近访问</h3>
      <div class="ai-grid small">
        <div v-for="ai in recentProviders" :key="ai.id" class="ai-card glass glass-hover mini" @click="openAI(ai)">
          <span class="ai-name">{{ ai.name }}</span>
        </div>
      </div>
    </div>

    <!-- Hidden -->
    <div v-if="hiddenProviders.length" class="section">
      <h3 class="section-label">👁 已隐藏</h3>
      <div class="ai-grid small">
        <div v-for="ai in hiddenProviders" :key="ai.id" class="ai-card glass glass-hover mini dimmed" @click="toggleEnable(ai)">
          <span class="ai-name">{{ ai.name }}</span>
          <span class="hidden-badge">点击启用</span>
        </div>
      </div>
    </div>

    <!-- Add/Edit Dialog -->
    <el-dialog v-model="showAdd" :title="editingAI ? '编辑 AI' : '添加 AI'" width="520px">
      <el-form :model="aiForm" label-position="top">
        <el-form-item label="名称 *">
          <el-input v-model="aiForm.name" placeholder="如: ChatGPT" />
        </el-form-item>
        <el-form-item label="网页 URL">
          <el-input v-model="aiForm.url" placeholder="https://chat.openai.com（直接打开的网页地址）" />
        </el-form-item>
        <el-form-item label="图标URL">
          <el-input v-model="aiForm.icon_url" placeholder="可选" />
        </el-form-item>
        <el-divider content-position="left">API 配置（可选 — 用于 API 聊天模式）</el-divider>
        <el-form-item label="API 类型">
          <el-select v-model="aiForm.api_type" style="width:100%">
            <el-option value="web" label="仅网页（无需 Key）" />
            <el-option value="openai" label="OpenAI 兼容" />
            <el-option value="deepseek" label="DeepSeek" />
            <el-option value="azure" label="Azure OpenAI" />
            <el-option value="claude" label="Claude (Anthropic)" />
            <el-option value="gemini" label="Gemini (Google)" />
            <el-option value="openrouter" label="OpenRouter" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="aiForm.api_type !== 'web'" label="API URL">
          <el-input v-model="aiForm.api_url" placeholder="https://api.openai.com/v1/chat/completions" />
        </el-form-item>
        <el-form-item v-if="aiForm.api_type !== 'web'" label="API Key">
          <el-input v-model="aiForm.api_key" type="password" show-password placeholder="sk-xxx（留空则只能使用网页模式）" />
          <span class="text-xs text-muted">✏️ 留空即可，不影响网页模式使用。填入后解锁 API 聊天。</span>
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
import { getAIProviders, createAIProvider, updateAIProvider, deleteAIProvider, sortAIProviders, recordAIVisit, getRecentAI } from '../api'
import draggable from 'vuedraggable'
import { ElMessage, ElMessageBox } from 'element-plus'

const providers = ref<any[]>([])
const recentProviders = ref<any[]>([])
const showAdd = ref(false)
const editingAI = ref<any>(null)
const aiForm = reactive({ name: '', url: '', icon_url: '', api_url: '', api_key: '', api_type: 'web' })

const pinnedProviders = computed(() => providers.value.filter(p => p.is_enabled && p.is_pinned))
const favoriteProviders = computed(() => providers.value.filter(p => p.is_enabled && p.is_favorite && !p.is_pinned))
const hiddenProviders = computed(() => providers.value.filter(p => !p.is_enabled))

const sortedProviders = computed({
  get: () => providers.value.filter(p => p.is_enabled && !p.is_pinned && !p.is_favorite).sort((a, b) => a.sort_order - b.sort_order),
  set: () => {},
})

async function fetchData() {
  const [all, recent] = await Promise.all([getAIProviders(), getRecentAI()])
  providers.value = all.data
  recentProviders.value = recent.data
}

function openAI(ai: any) {
  recordAIVisit(ai.id)
  window.open(ai.url, '_blank')
}

async function togglePin(ai: any) {
  await updateAIProvider(ai.id, { is_pinned: !ai.is_pinned })
  await fetchData()
}

async function toggleFavorite(ai: any) {
  await updateAIProvider(ai.id, { is_favorite: !ai.is_favorite })
  await fetchData()
}

async function toggleEnable(ai: any) {
  await updateAIProvider(ai.id, { is_enabled: !ai.is_enabled })
  await fetchData()
}

function openEdit(ai: any) {
  editingAI.value = ai
  aiForm.name = ai.name
  aiForm.url = ai.url
  aiForm.icon_url = ai.icon_url
  aiForm.api_type = ai.api_type
  aiForm.api_url = ai.api_url
  aiForm.api_key = ai.api_key
  showAdd.value = true
}

async function handleSave() {
  if (!aiForm.name || !aiForm.url) return
  if (editingAI.value) {
    await updateAIProvider(editingAI.value.id, { ...aiForm })
    ElMessage.success('已更新')
  } else {
    await createAIProvider({ ...aiForm, is_enabled: true })
    ElMessage.success('已添加')
  }
  showAdd.value = false
  editingAI.value = null
  aiForm.name = ''; aiForm.url = ''; aiForm.icon_url = ''
  aiForm.api_type = 'web'; aiForm.api_url = ''; aiForm.api_key = ''
  await fetchData()
}

async function handleDelete(ai: any) {
  try {
    await ElMessageBox.confirm(`确定删除 "${ai.name}"？`, '确认', { type: 'warning' })
    await deleteAIProvider(ai.id)
    ElMessage.success('已删除')
    await fetchData()
  } catch { /* cancelled */ }
}

async function onDragChange() {
  const items = sortedProviders.value.map((p: any, i: number) => ({ id: p.id, sort_order: i }))
  await sortAIProviders(items)
}

onMounted(fetchData)
</script>

<style scoped>
.ai-workspace {
  max-width: 1200px;
  margin: 0 auto;
}
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}
.page-header h2 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 22px;
  font-weight: 800;
}
.section {
  margin-bottom: 28px;
}
.section-label {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--text-secondary);
}
.ai-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
}
.ai-grid.small {
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
}
.ai-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 14px;
  cursor: pointer;
  position: relative;
}
.ai-card.mini {
  padding: 12px 14px;
  flex-direction: row;
  gap: 8px;
}
.ai-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: var(--accent-gradient);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 10px;
}
.ai-card.mini .ai-icon {
  width: 28px;
  height: 28px;
  font-size: 13px;
  margin-bottom: 0;
  border-radius: 8px;
}
.ai-name {
  font-size: 14px;
  font-weight: 500;
  text-align: center;
}
.ai-actions {
  display: flex;
  gap: 2px;
  margin-top: 8px;
  opacity: 0;
  transition: opacity var(--transition);
}
.ai-card:hover .ai-actions {
  opacity: 1;
}
.ai-card.mini .ai-actions {
  margin-top: 0;
  margin-left: auto;
}
.dimmed {
  opacity: 0.5;
}
.hidden-badge {
  font-size: 11px;
  color: var(--text-muted);
  margin-left: auto;
}

@media (max-width: 768px) {
  .ai-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
  }
}
</style>
