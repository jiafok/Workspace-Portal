<template>
  <div class="mobile-nav glass">
    <router-link v-for="item in navItems" :key="item.path" :to="item.path" :class="['mnav-item', { active: $route.path === item.path }]">
      <el-icon size="20"><component :is="item.icon" /></el-icon>
      <span>{{ item.label }}</span>
    </router-link>
  </div>
</template>

<script setup lang="ts">
const navItems = [
  { path: '/', label: '首页', icon: 'HomeFilled' },
  { path: '/ai-chat', label: 'AI', icon: 'ChatDotSquare' },
  { path: '/navigate', label: '导航', icon: 'Menu' },
  { path: '/docker', label: 'Docker', icon: 'Odometer' },
  { path: '/settings', label: '设置', icon: 'Setting' },
]
</script>

<style scoped>
.mobile-nav {
  display: none; position: fixed; bottom: 0; left: 0; right: 0;
  z-index: 200; padding: 6px 8px env(safe-area-inset-bottom, 8px);
  justify-content: space-around; border-radius: 0; border-top: 1px solid var(--border-color);
  border-bottom: none; border-left: none; border-right: none;
}
.mnav-item {
  display: flex; flex-direction: column; align-items: center; gap: 2px;
  padding: 6px 12px; border-radius: 10px; text-decoration: none;
  color: var(--text-muted); font-size: 11px; transition: all var(--transition);
}
.mnav-item.active { color: var(--accent); }
.mnav-item span { font-size: 10px; }
@media (max-width: 768px) { .mobile-nav { display: flex; } #app { padding-bottom: 72px; } }
</style>
