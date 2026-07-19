<template>
  <div class="tabs-bar glass" v-if="tabs.length > 0">
    <div v-for="tab in tabs" :key="tab.id" :class="['tab-item', { active: tab.id === activeTabId }]" @click="$emit('switch', tab.id)" @click.middle="$emit('close', tab.id)">
      <span class="tab-label">{{ tab.title }}</span>
      <el-button text size="small" class="tab-close" @click.stop="$emit('close', tab.id)"><el-icon size="12"><Close /></el-icon></el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ tabs: any[]; activeTabId: number | null }>()
defineEmits(['switch', 'close'])
</script>

<style scoped>
.tabs-bar {
  display: flex; gap: 2px; padding: 4px 8px; margin: 0 16px;
  overflow-x: auto; white-space: nowrap;
}
.tab-item {
  display: flex; align-items: center; gap: 6px; padding: 6px 12px;
  border-radius: 8px; cursor: pointer; font-size: 13px; color: var(--text-secondary);
  transition: all var(--transition); flex-shrink: 0;
}
.tab-item:hover { background: var(--bg-primary); color: var(--text-primary); }
.tab-item.active { background: var(--accent); color: white; }
.tab-close { padding: 2px; opacity: 0; transition: opacity 0.15s; }
.tab-item:hover .tab-close { opacity: 1; }
</style>
