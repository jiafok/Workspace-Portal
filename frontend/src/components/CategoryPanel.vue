<template>
  <div class="category-panel">
    <div class="category-header">
      <div class="cat-title">
        <el-icon size="16"><component :is="category.icon || 'Folder'" /></el-icon>
        <span>{{ category.name }}</span>
        <span class="cat-count">{{ websites.length }}</span>
      </div>
      <div class="cat-header-actions">
        <el-button text size="small" @click="$emit('add-website', category)">
          <el-icon><Plus /></el-icon>
        </el-button>
        <el-dropdown trigger="click" @command="(cmd: string) => handleCommand(cmd)">
          <el-button text size="small">
            <el-icon><MoreFilled /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="edit">
                <el-icon><Edit /></el-icon> 编辑分类
              </el-dropdown-item>
              <el-dropdown-item command="delete" divided>
                <el-icon><Delete /></el-icon> 删除分类
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
    <div :class="['websites-container', layoutMode]">
      <draggable
        :list="websites"
        :group="{ name: 'websites', pull: true, put: true }"
        item-key="id"
        :animation="200"
        ghost-class="sortable-ghost"
        chosen-class="sortable-chosen"
        drag-class="sortable-drag"
        @change="onDragChange"
        handle=".drag-handle"
      >
        <template #item="{ element }">
          <div class="website-item" @click="openWebsite(element)">
            <div class="drag-handle" v-if="showDragHandle">
              <el-icon size="14"><Rank /></el-icon>
            </div>
            <div class="icon-wrapper">
              <img v-if="element.icon_url && !imgErrors[element.id]" :src="element.icon_url" @error="imgErrors[element.id] = true" />
              <el-icon v-else><Link /></el-icon>
            </div>
            <div class="card-name">{{ element.name }}</div>
          </div>
        </template>
      </draggable>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { useSettingsStore } from '../stores/settings'
import { useNavigationStore } from '../stores/navigation'
import draggable from 'vuedraggable'

const props = defineProps<{ category: any; websites: any[] }>()
const emit = defineEmits(['add-website', 'refresh'])

const settingsStore = useSettingsStore()
const navigationStore = useNavigationStore()
const imgErrors = reactive<Record<number, boolean>>({})

const layoutMode = computed(() => settingsStore.layoutMode)
const showDragHandle = computed(() => settingsStore.layoutMode === 'list')

function handleCommand(cmd: string) {
  if (cmd === 'edit') emit('edit-category', props.category)
  else if (cmd === 'delete') emit('delete-category', props.category)
}

function openWebsite(web: any) {
  navigationStore.recordVisit(web.id)
  window.open(web.url, '_blank')
}

async function onDragChange(evt: any) {
  if (evt.moved || evt.added) {
    const items = props.websites.map((w, i) => ({
      id: w.id,
      sort_order: i,
      category_id: props.category.id,
    }))
    await navigationStore.reorderWebsites(items)
    emit('refresh')
  }
}
</script>

<style scoped>
.category-panel {
  margin-bottom: 24px;
}
.category-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 4px 12px;
}
.cat-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 700;
}
.cat-count {
  background: var(--bg-primary);
  padding: 0 8px;
  border-radius: 10px;
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 500;
}
.cat-header-actions {
  display: flex;
  gap: 4px;
}
.websites-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
  gap: 12px;
}
.websites-container.list {
  grid-template-columns: 1fr;
  gap: 6px;
}
.websites-container.desktop {
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 20px;
}

.website-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 10px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition);
  background: var(--bg-glass);
  border: 1px solid var(--border-color);
  position: relative;
}
.website-item:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-md);
  border-color: var(--accent-light);
}
.websites-container.list .website-item {
  flex-direction: row;
  padding: 10px 14px;
  gap: 12px;
}
.website-item .icon-wrapper {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
  font-size: 20px;
  background: var(--accent-gradient);
  color: white;
  flex-shrink: 0;
}
.websites-container.list .website-item .icon-wrapper {
  width: 32px;
  height: 32px;
  margin-bottom: 0;
  font-size: 16px;
  border-radius: 6px;
}
.website-item .icon-wrapper img {
  width: 24px;
  height: 24px;
  border-radius: 4px;
}
.website-item .card-name {
  font-size: 13px;
  text-align: center;
  line-height: 1.3;
  word-break: break-all;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.websites-container.list .website-item .card-name {
  font-size: 14px;
  text-align: left;
  -webkit-line-clamp: 1;
}

.drag-handle {
  cursor: grab;
  color: var(--text-muted);
  flex-shrink: 0;
}
.drag-handle:active {
  cursor: grabbing;
}

@media (max-width: 768px) {
  .websites-container {
    grid-template-columns: repeat(auto-fill, minmax(85px, 1fr));
    gap: 8px;
  }
  .website-item {
    padding: 12px 6px;
  }
  .website-item .icon-wrapper {
    width: 36px;
    height: 36px;
    font-size: 18px;
  }
}
</style>
