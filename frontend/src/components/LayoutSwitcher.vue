<template>
  <el-dropdown trigger="click" @command="handleCommand">
    <el-button text>
      <el-icon size="18">
        <Grid v-if="settingsStore.layoutMode === 'card'" />
        <List v-else-if="settingsStore.layoutMode === 'list'" />
        <Platform v-else-if="settingsStore.layoutMode === 'desktop'" />
        <Expand v-else />
      </el-icon>
      {{ layoutLabel }}
    </el-button>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item command="card">
          <el-icon><Grid /></el-icon> 卡片模式
        </el-dropdown-item>
        <el-dropdown-item command="list">
          <el-icon><List /></el-icon> 列表模式
        </el-dropdown-item>
        <el-dropdown-item command="desktop">
          <el-icon><Platform /></el-icon> 桌面模式
        </el-dropdown-item>
        <el-dropdown-item command="sidebar">
          <el-icon><Expand /></el-icon> 侧边栏模式
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useSettingsStore } from '../stores/settings'

const settingsStore = useSettingsStore()

const labels: Record<string, string> = {
  card: '卡片',
  list: '列表',
  desktop: '桌面',
  sidebar: '侧边栏',
}
const layoutLabel = computed(() => labels[settingsStore.layoutMode] || '卡片')

function handleCommand(mode: string) {
  settingsStore.setLayoutMode(mode as any)
}
</script>
