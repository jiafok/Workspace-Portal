<template>
  <div class="category-panel" :style="{ animationDelay: animationDelay }">
    <div class="cat-header">
      <div class="cat-icon-box" :style="{ background: catColor }">
        <el-icon size="18"><component :is="category.icon || 'Folder'" /></el-icon>
      </div>
      <div class="cat-text">
        <span class="cat-name">{{ category.name }}</span>
        <span class="cat-count">{{ websites.length }} 个网站</span>
      </div>
      <div class="cat-btns">
        <el-button size="small" round @click="$emit('add-website', category)">
          <el-icon><Plus /></el-icon> 添加
        </el-button>
        <el-dropdown trigger="click" @command="(cmd: string) => handleCommand(cmd)">
          <el-button size="small" round><el-icon><MoreFilled /></el-icon></el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="edit"><el-icon><Edit /></el-icon> 编辑分类</el-dropdown-item>
              <el-dropdown-item command="delete" divided><el-icon><Delete /></el-icon> 删除分类</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <div v-if="websites.length" class="site-grid">
      <div v-for="w in websites" :key="w.id" class="site-card glass glass-hover" @click="openWebsite(w)">
        <img v-if="w.icon_url" :src="w.icon_url" class="site-img" />
        <el-icon v-else class="site-fb" size="22"><Link /></el-icon>
        <div class="site-text">
          <span class="site-title">{{ w.name }}</span>
          <span class="site-url">{{ w.description || niceUrl(w.url) }}</span>
        </div>
        <span v-if="w.is_pinned" class="site-pin">📌</span>
      </div>
    </div>

    <div v-else class="cat-empty" @click="$emit('add-website', category)">
      <el-icon size="28"><Plus /></el-icon>
      <span>点击添加第一个网站</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useNavigationStore } from '../stores/navigation'

const props = defineProps<{ category: any; websites: any[]; index?: number }>()
const emit = defineEmits(['add-website', 'edit-category', 'delete-category', 'refresh'])
const nav = useNavigationStore()

const animationDelay = computed(() => `${(props.index ?? 0) * 0.06}s`)
const catColor = computed(() => {
  const c = ['#6c5ce7','#00b894','#0984e3','#e17055','#fdcb6e','#fd79a8','#636e72','#6c5ce7','#00cec9']
  return c[(props.index ?? 0) % c.length]
})

function handleCommand(cmd: string) {
  cmd === 'edit' ? emit('edit-category', props.category) : emit('delete-category', props.category)
}
function openWebsite(web: any) { nav.recordVisit(web.id); window.open(web.url, '_blank') }
function niceUrl(url: string) {
  try { return new URL(url.startsWith('http') ? url : 'https://' + url).hostname.replace('www.', '') }
  catch { return (url || '').replace(/https?:\/\//, '').split('/')[0].slice(0, 35) }
}
</script>

<style scoped>
.category-panel {
  opacity: 0;
  animation: fadeUp 0.45s ease forwards;
  animation-delay: v-bind(animationDelay);
  margin-bottom: 30px;
}
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}

.cat-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.cat-icon-box { width: 40px; height: 40px; border-radius: 14px; display: flex; align-items: center; justify-content: center; color: #fff; flex-shrink: 0; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
.cat-text { flex: 1; }
.cat-name { font-size: 18px; font-weight: 800; display: block; line-height: 1.3; }
.cat-count { font-size: 12px; color: var(--text-muted); }
.cat-btns { display: flex; gap: 4px; }

.site-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 10px;
}

.site-card {
  display: flex; align-items: center; gap: 12px;
  padding: 16px; border-radius: 16px;
  background: var(--bg-glass);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid rgba(255,255,255,0.08);
  cursor: pointer; position: relative;
  transition: all 0.25s ease;
}
.site-card:hover { transform: translateY(-3px); box-shadow: 0 8px 30px rgba(0,0,0,0.12); border-color: var(--accent-light); }
.site-img { width: 32px; height: 32px; border-radius: 8px; object-fit: contain; flex-shrink: 0; }
.site-fb { width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; background: var(--accent); color: #fff; flex-shrink: 0; }
.site-text { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 3px; }
.site-title { font-size: 14px; font-weight: 600; line-height: 1.3; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.site-url { font-size: 11px; color: var(--text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.site-pin { position: absolute; left: 10px; top: -4px; font-size: 12px; }

.cat-empty {
  display: flex; align-items: center; justify-content: center; gap: 10px;
  padding: 28px; border-radius: 16px;
  border: 2px dashed var(--border-color);
  cursor: pointer; color: var(--text-muted); font-size: 14px;
  transition: all 0.2s;
}
.cat-empty:hover { border-color: var(--accent); color: var(--accent); background: var(--bg-primary); }

@media (max-width: 768px) {
  .site-grid { grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); }
  .site-card { padding: 12px 14px; }
}
@media (max-width: 480px) {
  .site-grid { grid-template-columns: 1fr 1fr; }
}
</style>