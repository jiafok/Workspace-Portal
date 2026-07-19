<template>
  <div class="search-overlay" @click.self="settingsStore.toggleSearch()">
    <div class="search-panel glass" @click.stop>
      <div class="search-input-wrapper">
        <el-icon size="20" color="var(--accent)"><Search /></el-icon>
        <input
          ref="searchInput"
          v-model="query"
          placeholder="搜索网站、分类... (ESC 关闭)"
          class="search-input"
          @input="doSearch"
          @keydown="handleKey"
        />
      </div>
      <div v-if="query && (results.websites.length || results.categories.length)" class="search-results">
        <div v-if="results.categories.length" class="result-section">
          <div class="result-label">分类</div>
          <div
            v-for="cat in results.categories"
            :key="'c-' + cat.id"
            class="result-item"
          >
            <el-icon><Folder /></el-icon>
            <span>{{ cat.name }}</span>
          </div>
        </div>
        <div v-if="results.websites.length" class="result-section">
          <div class="result-label">网站</div>
          <div
            v-for="web in results.websites"
            :key="'w-' + web.id"
            class="result-item"
            @click="openWebsite(web)"
          >
            <img v-if="web.icon_url" :src="web.icon_url" class="result-icon" />
            <el-icon v-else><Link /></el-icon>
            <span class="result-name">{{ web.name }}</span>
            <span class="result-url">{{ web.url }}</span>
          </div>
        </div>
      </div>
      <div v-else-if="query" class="no-results">无匹配结果</div>
      <div v-else class="search-hint">
        <div>常用搜索</div>
        <div class="hint-tags">
          <span class="hint-tag" v-for="t in hotTags" :key="t" @click="query = t; doSearch()">{{ t }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useSettingsStore } from '../stores/settings'
import { useNavigationStore } from '../stores/navigation'

const settingsStore = useSettingsStore()
const navigationStore = useNavigationStore()

const query = ref('')
const searchInput = ref<HTMLInputElement | null>(null)
const results = ref({ websites: [] as any[], categories: [] as any[] })
let debounceTimer: number | null = null

const hotTags = ['GitHub', 'ChatGPT', 'Jira', 'Confluence', 'DSM', 'Portainer']

function doSearch() {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = window.setTimeout(async () => {
    if (!query.value.trim()) {
      results.value = { websites: [], categories: [] }
      return
    }
    await navigationStore.search(query.value.trim())
    results.value = navigationStore.searchResults
  }, 200)
}

function handleKey(e: KeyboardEvent) {
  if (e.key === 'Escape') settingsStore.toggleSearch()
}

function openWebsite(web: any) {
  navigationStore.recordVisit(web.id)
  window.open(web.url, '_blank')
  settingsStore.toggleSearch()
}

onMounted(async () => {
  await nextTick()
  searchInput.value?.focus()
})
</script>

<style scoped>
.search-input-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 18px;
  border-bottom: 1px solid var(--border-color);
}
.search-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 16px;
  color: var(--text-primary);
}
.search-input::placeholder {
  color: var(--text-muted);
}
.search-results {
  padding: 8px 0;
  max-height: 50vh;
  overflow-y: auto;
}
.result-section {
  margin-bottom: 4px;
}
.result-label {
  font-size: 11px;
  color: var(--text-muted);
  padding: 8px 18px 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.result-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 18px;
  cursor: pointer;
  transition: background var(--transition);
}
.result-item:hover {
  background: var(--bg-primary);
}
.result-icon {
  width: 20px;
  height: 20px;
  border-radius: 4px;
}
.result-name {
  font-weight: 500;
  font-size: 14px;
}
.result-url {
  font-size: 12px;
  color: var(--text-muted);
  margin-left: auto;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 200px;
}
.no-results, .search-hint {
  padding: 32px 18px;
  text-align: center;
  color: var(--text-muted);
}
.search-hint {
  font-size: 13px;
}
.hint-tags {
  display: flex;
  gap: 8px;
  justify-content: center;
  margin-top: 12px;
  flex-wrap: wrap;
}
.hint-tag {
  padding: 4px 14px;
  background: var(--bg-primary);
  border-radius: 20px;
  cursor: pointer;
  font-size: 12px;
  transition: all var(--transition);
}
.hint-tag:hover {
  background: var(--accent);
  color: white;
}
</style>
