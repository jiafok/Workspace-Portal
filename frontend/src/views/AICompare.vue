<template>
  <div class="ai-compare-page">
    <div class="page-header">
      <h2><el-icon><Connection /></el-icon> 多模型对比</h2>
      <span class="text-sm text-secondary">同时向多个 AI 发送相同问题，对比回答质量</span>
    </div>

    <!-- Provider Selection -->
    <div class="provider-select glass mb-4">
      <p class="text-sm text-muted mb-2">选择要对比的 AI（网页型 AI 将被跳过）</p>
      <el-checkbox-group v-model="selectedProviders" class="provider-grid">
        <el-checkbox v-for="p in chatProviders" :key="p.id" :value="p.id">
          {{ p.name }}
          <el-tag v-if="p.api_type==='web'" size="small" type="info">网页</el-tag>
          <el-tag v-else-if="!p.api_key" size="small" type="warning">未配置Key</el-tag>
        </el-checkbox>
      </el-checkbox-group>
    </div>

    <!-- Prompt Input -->
    <div class="prompt-input glass mb-4">
      <el-input v-model="userPrompt" type="textarea" :rows="4" placeholder="输入你的问题... 同时发送到选中的 AI 模型" />
      <div class="flex justify-end mt-3 gap-2">
        <el-button @click="showPromptPicker = true"><el-icon><Document /></el-icon> 使用 Prompt</el-button>
        <el-button type="primary" @click="runCompare" :loading="comparing" :disabled="!selectedProviders.length">
          <el-icon><Promotion /></el-icon> 发送到 {{ selectedProviders.length }} 个模型
        </el-button>
      </div>
    </div>

    <!-- Results Grid -->
    <div v-if="results.length" class="results-grid">
      <div v-for="r in results" :key="r.provider_id" class="result-card glass">
        <div class="result-header">
          <span class="font-bold">{{ r.provider_name }}</span>
          <el-tag v-if="r.error" type="danger" size="small">错误</el-tag>
          <el-button text size="small" @click="copyText(r.content)"><el-icon><CopyDocument /></el-icon></el-button>
        </div>
        <div class="result-content" v-html="renderMarkdown(r.content)"></div>
      </div>
    </div>

    <!-- Prompt picker -->
    <el-dialog v-model="showPromptPicker" title="选择 Prompt" width="500px">
      <el-input v-model="promptSearch" placeholder="搜索..." class="mb-3" />
      <div class="prompt-list-dialog">
        <div v-for="p in filteredPrompts" :key="p.id" class="prompt-option" @click="usePrompt(p)">
          <b>{{ p.title }}</b><span class="text-xs text-muted">{{ p.category }}</span>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { aiCompare, getAIProviders, getPrompts } from '../api'
import MarkdownIt from 'markdown-it'
import { ElMessage } from 'element-plus'

const md = new MarkdownIt({ breaks: true, linkify: true })

const chatProviders = ref<any[]>([])
const selectedProviders = ref<number[]>([])
const userPrompt = ref('')
const results = ref<any[]>([])
const comparing = ref(false)
const showPromptPicker = ref(false)
const promptSearch = ref('')
const allPrompts = ref<any[]>([])

const filteredPrompts = computed(() => {
  if (!promptSearch.value) return allPrompts.value
  return allPrompts.value.filter((p: any) => p.title.toLowerCase().includes(promptSearch.value.toLowerCase()))
})

function renderMarkdown(text: string) { return md.render(text || '') }
function copyText(text: string) { navigator.clipboard.writeText(text); ElMessage.success('已复制') }

async function runCompare() {
  if (!userPrompt.value.trim() || !selectedProviders.value.length) return
  comparing.value = true; results.value = []
  try {
    const { data } = await aiCompare({
      prompt: userPrompt.value,
      provider_ids: selectedProviders.value,
    })
    results.value = data.results
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '对比失败')
  }
  comparing.value = false
}

async function insertPrompt() {
  showPromptPicker.value = true
  const { data } = await getPrompts()
  allPrompts.value = data
}
function usePrompt(p: any) {
  userPrompt.value = p.content; showPromptPicker.value = false
}

onMounted(async () => {
  try {
    const { data } = await getAIProviders()
    chatProviders.value = data.filter((p: any) => p.is_enabled)
  } catch { /* */ }
})
</script>

<style scoped>
.ai-compare-page { max-width: 1400px; margin: 0 auto; }
.page-header { margin-bottom: 20px; display: flex; align-items: center; gap: 12px; }
.page-header h2 { display: flex; align-items: center; gap: 8px; font-size: 22px; font-weight: 800; }
.provider-select { padding: 16px 20px; }
.provider-grid { display: flex; flex-wrap: wrap; gap: 12px; }
.prompt-input { padding: 16px 20px; }
.results-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 14px; margin-top: 16px; }
.result-card { padding: 18px; }
.result-header { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.result-content { font-size: 14px; line-height: 1.7; overflow-wrap: break-word; max-height: 500px; overflow-y: auto; }
.result-content :deep(pre) { background: var(--bg-primary); padding: 10px; border-radius: 6px; font-size: 12px; overflow-x: auto; }
.prompt-list-dialog { max-height: 300px; overflow-y: auto; }
.prompt-option { padding: 12px; border-radius: 8px; cursor: pointer; border: 1px solid var(--border-color); margin-bottom: 6px; display: flex; justify-content: space-between; }
.prompt-option:hover { background: var(--bg-primary); }
</style>
