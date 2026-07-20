<template>
  <div class="plugin-market">
    <div class="page-header">
      <h2><el-icon><Grid /></el-icon> 插件市场</h2>
      <div class="header-actions">
        <el-select v-model="filterCategory" placeholder="分类筛选" clearable size="default" style="width:140px">
          <el-option v-for="c in categories" :key="c.value" :value="c.value" :label="c.label">
            <el-icon><component :is="c.icon" /></el-icon> {{ c.label }}
          </el-option>
        </el-select>
      </div>
    </div>

    <div v-loading="loading" class="plugin-grid">
      <div v-for="p in filteredPlugins" :key="p.plugin_id" class="plugin-card glass glass-hover">
        <div class="plugin-top">
          <div class="plugin-icon" :style="{ background: iconColor(p.category) }">
            <el-icon size="22"><component :is="iconForCat(p.category)" /></el-icon>
          </div>
          <div class="plugin-main">
            <h4>{{ p.name }}</h4>
            <span class="plugin-ver">v{{ p.version }} · {{ p.author }}</span>
            <el-tag v-if="p.is_builtin" size="small" type="info">内置</el-tag>
          </div>
          <el-switch :model-value="p.is_enabled" @change="(v) => togglePlugin(p, v)" />
        </div>
        <p class="plugin-desc">{{ p.description }}</p>
        <div class="plugin-actions" v-if="p.config_schema && p.config_schema !== '{}'">
          <el-button size="small" @click="openConfig(p)">
            <el-icon><Setting /></el-icon> 配置
          </el-button>
        </div>
      </div>
      <el-empty v-if="!loading && !filteredPlugins.length" description="暂无插件" />
    </div>

    <!-- Config Dialog -->
    <el-dialog v-model="showConfig" :title="`配置 - ${configPlugin?.name}`" width="520px" @close="configPlugin = null">
      <el-form v-if="configPlugin" label-position="top">
        <el-form-item v-for="(_, key) in configData" :key="key" :label="key">
          <el-input v-if="key !== 'password' && key !== 'access_token' && key !== 'api_key'"
            v-model="configData[key]" :placeholder="`输入 ${key}`" />
          <el-input v-else v-model="configData[key]" type="password" show-password :placeholder="`输入 ${key}`" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showConfig = false">取消</el-button>
        <el-button type="primary" @click="saveConfig">保存配置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import api from '../api'
import { ElMessage } from 'element-plus'

interface Plugin { plugin_id: string; name: string; version: string; author: string; description: string; category: string; is_enabled: boolean; is_builtin: boolean; config_schema: string; config_data: string; }
const plugins = ref<Plugin[]>([])
const loading = ref(false)
const filterCategory = ref('')
const showConfig = ref(false)
const configPlugin = ref<Plugin | null>(null)
const configData = reactive<Record<string, string>>({})

const categories = [
  { value: 'tool', label: '工具', icon: 'Tools' },
  { value: 'integration', label: '集成', icon: 'Connection' },
  { value: 'monitoring', label: '监控', icon: 'Odometer' },
  { value: 'theme', label: '主题', icon: 'Brush' },
  { value: 'widget', label: '组件', icon: 'Grid' },
]

const filteredPlugins = computed(() => {
  if (!filterCategory.value) return plugins.value
  return plugins.value.filter(p => p.category === filterCategory.value)
})

function iconForCat(cat: string) {
  const m: Record<string, string> = { tool: 'Tools', integration: 'Connection', monitoring: 'Odometer', theme: 'Brush', widget: 'Grid' }
  return m[cat] || 'Tools'
}
function iconColor(cat: string) {
  const m: Record<string, string> = { tool: '#6c5ce7', integration: '#0984e3', monitoring: '#00b894', theme: '#e17055', widget: '#fdcb6e' }
  return `linear-gradient(135deg, ${m[cat] || '#6c5ce7'}, ${m[cat] || '#a29bfe'}88)`
}

async function fetchPlugins() { loading.value = true; try { const { data } = await api.get('/plugins'); plugins.value = data } catch { /* */ }; loading.value = false }
async function togglePlugin(p: Plugin, v: boolean) {
  await api.put(`/plugins/${p.plugin_id}/toggle`, {})
  p.is_enabled = v; ElMessage.success(v ? `${p.name} 已启用` : `${p.name} 已禁用`)
}

function openConfig(p: Plugin) {
  configPlugin.value = p
  // 清空所有旧的 keys
  Object.keys(configData).forEach(k => delete configData[k])
  // 从 schema 读取 defaults
  if (p.config_schema && p.config_schema.trim()) {
    try {
      const schema = JSON.parse(p.config_schema)
      if (typeof schema === 'object') {
        Object.entries(schema).forEach(([k, v]) => {
          configData[k] = v || ''
        })
      }
    } catch (e) {
      console.error('Failed to parse config_schema:', e)
    }
  }
  // 从 config_data 覆盖
  if (p.config_data && p.config_data.trim()) {
    try {
      const data = JSON.parse(p.config_data)
      if (typeof data === 'object') {
        Object.entries(data).forEach(([k, v]) => {
          configData[k] = v || ''
        })
      }
    } catch (e) {
      console.error('Failed to parse config_data:', e)
    }
  }
  showConfig.value = true
}

async function saveConfig() {
  if (!configPlugin.value) return
  await api.put(`/plugins/${configPlugin.value.plugin_id}/config`, { config_data: { ...configData } })
  ElMessage.success('配置已保存'); showConfig.value = false
}

onMounted(fetchPlugins)
</script>

<style scoped>
.plugin-market { max-width: 1100px; margin: 0 auto; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.page-header h2 { display: flex; align-items: center; gap: 8px; font-size: 22px; font-weight: 800; }
.header-actions { display: flex; gap: 8px; }
.plugin-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 14px; }
.plugin-card { padding: 18px 20px; }
.plugin-top { display: flex; align-items: flex-start; gap: 12px; }
.plugin-icon { width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; color: white; flex-shrink: 0; }
.plugin-main { flex: 1; }
.plugin-main h4 { font-size: 16px; font-weight: 700; margin-bottom: 4px; }
.plugin-ver { font-size: 12px; color: var(--text-muted); }
.plugin-desc { font-size: 13px; color: var(--text-secondary); margin-top: 10px; line-height: 1.5; }
.plugin-actions { margin-top: 10px; }
@media (max-width: 768px) { .plugin-grid { grid-template-columns: 1fr; } }
</style>
