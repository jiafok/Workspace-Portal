<template>
  <div class="command-palette-overlay" @click.self="$emit('close')">
    <div class="command-palette glass" @click.stop>
      <div class="cp-input-wrapper">
        <el-icon size="20" color="var(--accent)"><Search /></el-icon>
        <input ref="inputRef" v-model="query" placeholder="搜索或输入命令... (ESC 关闭)" class="cp-input" @keydown="handleKey" />
        <kbd>ESC</kbd>
      </div>

      <div class="cp-results" v-if="query">
        <!-- Quick Actions -->
        <div class="cp-section" v-if="filteredActions.length">
          <div class="cp-section-label">⚡ 快捷操作</div>
          <div v-for="act in filteredActions" :key="act.id" class="cp-item" @click="runAction(act)">
            <div class="cp-icon" :style="{ background: act.color }"><el-icon size="16"><component :is="act.icon" /></el-icon></div>
            <div class="cp-info">
              <span class="cp-name">{{ act.label }}</span>
              <span class="cp-desc">{{ act.desc }}</span>
            </div>
            <span class="cp-shortcut" v-if="act.shortcut">{{ act.shortcut }}</span>
          </div>
        </div>

        <!-- Websites -->
        <div class="cp-section" v-if="filteredWebsites.length">
          <div class="cp-section-label">🔗 网站</div>
          <div v-for="w in filteredWebsites.slice(0, 6)" :key="'w-' + w.id" class="cp-item" @click="openWeb(w)">
            <img v-if="w.icon_url" :src="w.icon_url" class="cp-img" />
            <el-icon v-else size="16"><Link /></el-icon>
            <span class="cp-name">{{ w.name }}</span>
            <span class="cp-url">{{ w.url }}</span>
          </div>
        </div>

        <!-- AI -->
        <div class="cp-section" v-if="filteredAI.length">
          <div class="cp-section-label">🤖 AI 工具</div>
          <div v-for="a in filteredAI.slice(0, 4)" :key="'a-' + a.id" class="cp-item" @click="openAI(a)">
            <span class="cp-name">{{ a.name }}</span>
          </div>
        </div>

        <div v-if="!hasResults" class="cp-empty">无匹配结果</div>
      </div>

      <div v-else class="cp-recent">
        <div class="cp-section-label">🕐 最近访问</div>
        <div v-for="w in recentSites.slice(0, 8)" :key="'r-' + w.id" class="cp-item" @click="openWeb(w)">
          <span class="cp-name">{{ w.name }}</span>
          <span class="cp-shortcut">{{ w.category?.name }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useNavigationStore } from '../stores/navigation'
import { getRecentWebsites, getAIProviders, recordVisit, recordAIVisit } from '../api'

const emit = defineEmits(['close'])
const router = useRouter()
const navigationStore = useNavigationStore()

const query = ref('')
const inputRef = ref<HTMLInputElement | null>(null)
const recentSites = ref<any[]>([])
const allAI = ref<any[]>([])

const actions = [
  { id: 'nav-manager', label: '打开导航管理', desc: '管理网站和分类', icon: 'Menu', color: 'linear-gradient(135deg, #6c5ce7, #a29bfe)', shortcut: '', action: () => router.push('/navigate') },
  { id: 'ai-chat', label: 'AI 对话', desc: '打开 AI 聚合聊天', icon: 'ChatDotSquare', color: 'linear-gradient(135deg, #00b894, #55efc4)', shortcut: '', action: () => router.push('/ai-chat') },
  { id: 'ai-compare', label: '多模型对比', desc: '同时对比多个 AI', icon: 'Connection', color: 'linear-gradient(135deg, #0984e3, #74b9ff)', shortcut: '', action: () => router.push('/ai-compare') },
  { id: 'docker', label: 'Docker 监控', desc: '查看和管理容器', icon: 'Odometer', color: 'linear-gradient(135deg, #e17055, #fab1a0)', shortcut: '', action: () => router.push('/docker') },
  { id: 'plugins', label: '插件市场', desc: '浏览和配置插件', icon: 'Grid', color: 'linear-gradient(135deg, #fdcb6e, #ffeaa7)', shortcut: '', action: () => router.push('/plugins') },
  { id: 'theme-toggle', label: '切换深色模式', desc: '切换界面主题', icon: 'Moon', color: 'linear-gradient(135deg, #636e72, #b2bec3)', shortcut: '', action: () => { /* handled by app */ } },
  { id: 'settings', label: '系统设置', desc: '配置系统参数', icon: 'Setting', color: 'linear-gradient(135deg, #636e72, #b2bec3)', shortcut: '', action: () => router.push('/settings') },
]

const filteredActions = computed(() => {
  if (!query.value) return actions.slice(0, 4)
  const q = query.value.toLowerCase()
  return actions.filter(a => a.label.toLowerCase().includes(q) || a.desc.toLowerCase().includes(q))
})

const filteredWebsites = computed(() => {
  if (!query.value) return []
  const q = query.value.toLowerCase()
  return navigationStore.websites.filter(w => w.name.toLowerCase().includes(q) || w.url.toLowerCase().includes(q))
})

const filteredAI = computed(() => {
  if (!query.value) return []
  const q = query.value.toLowerCase()
  return allAI.value.filter((a: any) => a.name.toLowerCase().includes(q))
})

const hasResults = computed(() => filteredActions.value.length || filteredWebsites.value.length || filteredAI.value.length)

function handleKey(e: KeyboardEvent) {
  if (e.key === 'Escape') emit('close')
  if (e.key === 'Enter' && filteredActions.value.length) {
    runAction(filteredActions.value[0])
  }
}

function runAction(act: any) {
  if (act.action) act.action()
  emit('close')
}

function openWeb(w: any) { recordVisit(w.id); window.open(w.url, '_blank'); emit('close') }
function openAI(a: any) { recordAIVisit(a.id); window.open(a.url, '_blank'); emit('close') }

onMounted(async () => {
  await nextTick(); inputRef.value?.focus()
  try { const { data } = await getRecentWebsites(8); recentSites.value = data } catch { /* */ }
  try { const { data } = await getAIProviders(); allAI.value = data } catch { /* */ }
})
</script>

<style scoped>
.command-palette-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.6); backdrop-filter: blur(10px); z-index: 10000; display: flex; justify-content: center; padding-top: 12vh; }
.command-palette { width: 600px; max-height: 70vh; overflow-y: auto; max-width: 95vw; }
.cp-input-wrapper { display: flex; align-items: center; gap: 10px; padding: 14px 18px; border-bottom: 1px solid var(--border-color); }
.cp-input { flex: 1; border: none; outline: none; background: transparent; font-size: 17px; color: var(--text-primary); }
.cp-input::placeholder { color: var(--text-muted); }
.cp-section { padding: 4px 0; }
.cp-section-label { font-size: 11px; color: var(--text-muted); padding: 8px 18px 4px; text-transform: uppercase; letter-spacing: 0.5px; }
.cp-item { display: flex; align-items: center; gap: 10px; padding: 10px 18px; cursor: pointer; transition: background 0.15s; }
.cp-item:hover { background: var(--bg-primary); }
.cp-icon { width: 28px; height: 28px; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; flex-shrink: 0; }
.cp-img { width: 20px; height: 20px; border-radius: 4px; }
.cp-info { flex: 1; }
.cp-name { font-size: 14px; font-weight: 500; }
.cp-desc { font-size: 12px; color: var(--text-muted); display: block; }
.cp-url { font-size: 12px; color: var(--text-muted); margin-left: auto; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.cp-shortcut { font-size: 11px; color: var(--text-muted); background: var(--bg-primary); padding: 2px 8px; border-radius: 4px; }
.cp-empty, .cp-recent { padding: 24px; text-align: center; color: var(--text-muted); font-size: 13px; }
</style>
