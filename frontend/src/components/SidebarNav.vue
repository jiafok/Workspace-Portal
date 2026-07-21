<template>
  <nav class="sidebar-nav">
    <div class="nav-header">
      <span class="logo-text">⚡ Portal</span>
    </div>
    <div class="nav-links">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="nav-link"
        :class="{ active: $route.path === item.path }"
        @click="$emit('navigate')"
      >
        <el-icon size="18"><component :is="item.icon" /></el-icon>
        <span>{{ item.label }}</span>
      </router-link>
    </div>
    <div class="nav-footer">
      <span class="version">v1.0.0</span>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '../stores/auth'

defineEmits(['navigate'])

const authStore = useAuthStore()

const allNavItems = [
  { path: '/', label: '工作台首页', icon: 'HomeFilled' },
  { path: '/ai-chat', label: 'AI 对话', icon: 'ChatDotSquare' },
  { path: '/ai-compare', label: '多模型对比', icon: 'Connection' },
  { path: '/ai', label: 'AI 工具', icon: 'MagicStick' },
  { path: '/prompts', label: 'Prompt 中心', icon: 'Document' },
  { path: '/navigate', label: '导航管理', icon: 'Menu' },
  { path: '/enterprise', label: '企业系统', icon: 'OfficeBuilding' },
  { path: '/documents', label: '文档中心', icon: 'Files' },
  { path: '/nas', label: 'NAS 中心', icon: 'Monitor' },
  { path: '/docker', label: 'Docker 监控', icon: 'Odometer' },
  { path: '/plugins', label: '插件市场', icon: 'Grid' },
  { path: '/monitoring', label: '端点监控', icon: 'Odometer' },
  { path: '/github', label: '代码平台', icon: 'Connection' },
  { path: '/webhooks', label: 'Webhook', icon: 'Link' },
  { path: '/notifications', label: '通知中心', icon: 'Bell' },
  { path: '/audit', label: '审计日志', icon: 'DocumentChecked' },
  { path: '/data', label: '数据管理', icon: 'FolderOpened' },
  { path: '/personalize', label: '个性化', icon: 'Brush' },
  { path: '/settings', label: '系统设置', icon: 'Setting' },
]

const navItems = computed(() => {
  if (authStore.user?.role === 'admin') return allNavItems
  // Non-admin: filter by page visibility config
  const visible = authStore.visiblePages
  if (!visible || !visible.length) return allNavItems
  return allNavItems.filter(item => visible.includes(item.path))
})
</script>

<style scoped>
.sidebar-nav {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 20px 12px;
}
.nav-header {
  padding: 8px 12px 24px;
}
.logo-text {
  font-size: 22px;
  font-weight: 800;
  background: var(--accent-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.nav-links {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.nav-link {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 10px;
  text-decoration: none;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  transition: all var(--transition);
}
.nav-link:hover {
  background: var(--bg-primary);
  color: var(--text-primary);
}
.nav-link.active {
  background: var(--accent);
  color: white;
}
.nav-footer {
  padding: 12px;
  text-align: center;
}
.version {
  font-size: 11px;
  color: var(--text-muted);
}
</style>
