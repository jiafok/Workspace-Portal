<template>
  <div class="category-panel" :style="{ animationDelay: animationDelay }">
    <div class="category-header">
      <div class="cat-title-row">
        <div class="cat-icon" :style="{ background: catColor }">
          <el-icon size="18"><component :is="category.icon || 'Folder'" /></el-icon>
        </div>
        <div class="cat-info">
          <span class="cat-name">{{ category.name }}</span>
          <span class="cat-count">{{ websites.length }} 个网站</span>
        </div>
        <div class="cat-actions">
          <el-button size="small" round @click="$emit('add-website', category)">
            <el-icon><Plus /></el-icon> 添加
          </el-button>
          <el-dropdown trigger="click" @command="(cmd: string) => handleCommand(cmd)">
            <el-button size="small" round>
              <el-icon><MoreFilled /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="edit"><el-icon><Edit /></el-icon> 编辑分类</el-dropdown-item>
                <el-dropdown-item command="delete" divided><el-icon><Delete /></el-icon> 删除分类</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </div>

    <draggable
      v-if="websites.length"
      :list="websites"
      :group="{ name: 'websites', pull: true, put: true }"
      item-key="id"
      :animation="200"
      ghost-class="sortable-ghost"
      chosen-class="sortable-chosen"
      drag-class="sortable-drag"
      @change="onDragChange"
      class="card-grid"
    >
      <template #item="{ element }">
        <div class="site-card" @click="openWebsite(element)">
          <div class="site-icon-wrap">
            <img v-if="element.icon_url && !imgErrors[element.id]" :src="element.icon_url" @error="imgErrors[element.id] = true" />
            <span v-else class="site-fallback-icon">{{ element.name[0] }}</span>
          </div>
          <div class="site-body">
            <span class="site-name">{{ element.name }}</span>
            <span class="site-sub">{{ element.description ? truncate(element.description, 40) : niceUrl(element.url) }}</span>
          </div>
          <div v-if="element.is_pinned" class="pin-badge">📌</div>
        </div>
      </template>
    </draggable>

    <div v-else class="empty-category" @click="$emit('add-website', category)">
      <el-icon size="28"><Plus /></el-icon>
      <span>点击添加第一个网站</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive } from 'vue'
import { useNavigationStore } from '../stores/navigation'
import draggable from 'vuedraggable'

const props = defineProps<{ category: any; websites: any[]; index?: number }>()
const emit = defineEmits(['add-website', 'edit-category', 'delete-category', 'refresh'])
const navigationStore = useNavigationStore()
const imgErrors = reactive<Record<number, boolean>>({})

const animationDelay = computed(() => `${(props.index || 0) * 0.06}s`)
const catColor = computed(() => {
  const colors = ['linear-gradient(135deg,#6c5ce7,#a29bfe)','linear-gradient(135deg,#00b894,#55efc4)','linear-gradient(135deg,#0984e3,#74b9ff)','linear-gradient(135deg,#e17055,#fab1a0)','linear-gradient(135deg,#fdcb6e,#ffeaa7)','linear-gradient(135deg,#fd79a8,#fab1a0)','linear-gradient(135deg,#636e72,#b2bec3)','linear-gradient(135deg,#6c5ce7,#fd79a8)','linear-gradient(135deg,#00cec9,#55efc4)']
  return colors[(props.index || 0) % colors.length]
})

function handleCommand(cmd: string) { cmd === 'edit' ? emit('edit-category', props.category) : emit('delete-category', props.category) }
function openWebsite(web: any) { navigationStore.recordVisit(web.id); window.open(web.url, '_blank') }
function truncate(t: string, n: number) { return t && t.length > n ? t.slice(0, n) + '...' : (t || '') }
function niceUrl(url: string) { try { return new URL(url.startsWith('http') ? url : 'https://' + url).hostname.replace('www.', '') } catch { return url.replace(/https?:\/\//, '').replace('www.', '').slice(0, 30) } }

async function onDragChange(evt: any) {
  if (evt.moved || evt.added) {
    await navigationStore.reorderWebsites(props.websites.map((w, i) => ({ id: w.id, sort_order: i, category_id: props.category.id })))
    emit('refresh')
  }
}
</script>

<style scoped>
.category-panel {
  animation: fadeSlideIn 0.5s ease forwards;
  animation-delay: v-bind(animationDelay);
  opacity: 0;
  margin-bottom: 28px;
}
@keyframes fadeSlideIn {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}

.category-header { margin-bottom: 14px; }
.cat-title-row { display: flex; align-items: center; gap: 12px; }
.cat-icon { width: 38px; height: 38px; border-radius: 12px; display: flex; align-items: center; justify-content: center; color: white; flex-shrink: 0; }
.cat-info { flex: 1; }
.cat-name { font-size: 17px; font-weight: 800; display: block; line-height: 1.2; }
.cat-count { font-size: 12px; color: var(--text-muted); font-weight: 400; }
.cat-actions { display: flex; gap: 4px; }

/* ---- GRID LAYOUT ---- */
.card-grid {
  display: grid !important;
  grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)) !important;
  gap: 10px;
}
.card-grid > div { display: contents !important; }

.site-card {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 16px; border-radius: 14px;
  background: var(--bg-glass); backdrop-filter: blur(10px);
  border: 1px solid var(--border-color);
  cursor: pointer; position: relative; overflow: hidden;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.site-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.1); border-color: var(--accent-light); }

.site-icon-wrap { width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; background: var(--bg-primary); overflow: hidden; }
.site-icon-wrap img { width: 28px; height: 28px; border-radius: 6px; object-fit: contain; }
.site-fallback-icon { font-size: 20px; font-weight: 800; background: var(--accent-gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.site-body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.site-name { font-size: 14px; font-weight: 600; line-height: 1.3; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.site-sub { font-size: 11px; color: var(--text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pin-badge { position: absolute; left: 8px; top: -2px; font-size: 12px; }

.empty-category { display: flex; align-items: center; justify-content: center; gap: 8px; padding: 24px; border-radius: 14px; border: 2px dashed var(--border-color); cursor: pointer; color: var(--text-muted); font-size: 14px; transition: all 0.2s; }
.empty-category:hover { border-color: var(--accent-light); color: var(--accent); background: var(--bg-primary); }

.sortable-ghost { opacity: 0.3; border: 2px dashed var(--accent) !important; }
.sortable-chosen { box-shadow: 0 12px 32px rgba(0,0,0,0.15) !important; z-index: 100; }

@media (max-width: 768px) { .card-grid { grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)) !important; } .site-card { padding: 12px 14px; } .site-icon-wrap { width: 38px; height: 38px; } }
@media (max-width: 480px) { .card-grid { grid-template-columns: 1fr 1fr !important; } }
</style>
