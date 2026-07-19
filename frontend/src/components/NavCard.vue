<template>
  <div
    :class="['nav-card', 'glass', 'glass-hover', { 'list-mode': isListMode }]"
  >
    <div class="icon-wrapper">
      <img v-if="website.icon_url" :src="website.icon_url" @error="imgError = true" />
      <el-icon v-else-if="imgError || !website.icon_url"><Link /></el-icon>
    </div>
    <div class="card-name">{{ website.name }}</div>
    <div v-if="isListMode" class="list-extra">
      <span class="card-desc">{{ website.description || website.url }}</span>
      <div class="card-actions">
        <el-button text size="small" @click.stop="$emit('edit', website)">
          <el-icon><Edit /></el-icon>
        </el-button>
        <el-button text size="small" @click.stop="$emit('delete', website)">
          <el-icon><Delete /></el-icon>
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useSettingsStore } from '../stores/settings'

const props = defineProps<{ website: any }>()
defineEmits(['edit', 'delete'])

const settingsStore = useSettingsStore()
const imgError = ref(false)
const isListMode = computed(() => settingsStore.layoutMode === 'list')
</script>

<style scoped>
.list-extra {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-width: 0;
}
.card-desc {
  font-size: 12px;
  color: var(--text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.card-actions {
  display: flex;
  gap: 4px;
}
</style>
