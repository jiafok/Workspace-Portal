<template>
  <Login v-if="!authStore.isAuthenticated && !authLoading" />
  <div v-else-if="!authLoading" :class="['app-container', layoutMode]">
    <aside v-if="layoutMode === 'sidebar'" class="sidebar glass"><SidebarNav /></aside>
    <div class="main-area">
      <header class="top-bar glass">
        <div class="top-left">
          <el-button v-if="layoutMode !== 'sidebar'" text @click="settingsStore.toggleSidebar()">
            <el-icon size="20"><Expand /></el-icon>
          </el-button>
          <h1 class="app-title">🚀 Workspace Portal</h1>
        </div>
        <div class="top-center">
          <div class="global-search" @click="showCommandPalette = true">
            <el-icon><Search /></el-icon>
            <span class="search-placeholder">搜索网站、分类、AI、文档或输入命令...</span>
            <kbd>Ctrl+K</kbd>
          </div>
        </div>
        <div class="top-right">
          <!-- Weather -->
          <WeatherWidget />
          <!-- Notifications -->
          <el-badge :value="unreadNotifCount" :hidden="!unreadNotifCount" :max="99">
            <el-button text circle @click="router.push('/notifications')">
              <el-icon size="18"><Bell /></el-icon>
            </el-button>
          </el-badge>
          <!-- Language -->
          <el-button text circle @click="toggleLang" :title="i18nStore.locale === 'zh-CN' ? 'Switch to English' : '切换到中文'">
            <span style="font-size:13px;font-weight:700">{{ i18nStore.locale === 'zh-CN' ? '中' : 'EN' }}</span>
          </el-button>
          <!-- Theme -->
          <el-tooltip :content="isDark ? '浅色模式' : '深色模式'" placement="bottom">
            <el-button text circle @click="toggleTheme">
              <el-icon size="18"><Sunny v-if="isDark" /><Moon v-else /></el-icon>
            </el-button>
          </el-tooltip>
          <!-- Layout -->
          <LayoutSwitcher />
          <!-- User -->
          <el-dropdown trigger="click" @command="handleUserCommand">
            <el-button text class="user-btn">
              <el-icon size="16"><UserFilled /></el-icon>
              <span class="username">{{ authStore.user?.display_name || authStore.user?.username }}</span>
              <el-tag :type="roleTagType" size="small" class="role-tag">{{ roleLabel }}</el-tag>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item disabled><span style="font-size:12px;color:var(--text-muted)">{{ authStore.user?.email }}</span></el-dropdown-item>
                <el-dropdown-item command="settings"><el-icon><Setting /></el-icon> 系统设置</el-dropdown-item>
                <el-dropdown-item divided command="logout"><el-icon><SwitchButton /></el-icon> 退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <DashboardStrip />
      <TabsBar :tabs="tabStore.tabs" :active-tab-id="tabStore.activeTabId" @switch="tabStore.switchTab" @close="tabStore.closeTab" />

      <main class="page-content">
        <router-view v-slot="{ Component, route }">
          <transition name="fade" mode="out-in">
            <component :is="Component" :key="route.path" />
          </transition>
        </router-view>
      </main>
      <MobileBottomNav />
    </div>

    <el-drawer v-model="settingsStore.sidebarCollapsed" direction="ltr" size="260px" :with-header="false">
      <SidebarNav @navigate="settingsStore.sidebarCollapsed = false" />
    </el-drawer>

    <CommandPalette v-if="showCommandPalette" @close="showCommandPalette = false" />
  </div>

  <div v-else class="loading-screen"><el-icon size="40" class="loading-spin"><Loading /></el-icon></div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useSettingsStore } from './stores/settings'
import { useDashboardStore } from './stores/dashboard'
import { useAuthStore } from './stores/auth'
import { useI18nStore } from './stores/i18n'
import { useTabStore } from './stores/tabs'
import SidebarNav from './components/SidebarNav.vue'
import LayoutSwitcher from './components/LayoutSwitcher.vue'
import DashboardStrip from './components/DashboardStrip.vue'
import CommandPalette from './components/CommandPalette.vue'
import MobileBottomNav from './components/MobileBottomNav.vue'
import WeatherWidget from './components/WeatherWidget.vue'
import TabsBar from './components/TabsBar.vue'
import Login from './views/Login.vue'
import api from './api'

const settingsStore = useSettingsStore()
const dashboardStore = useDashboardStore()
const authStore = useAuthStore()
const i18nStore = useI18nStore()
const tabStore = useTabStore()
const router = useRouter()
const showCommandPalette = ref(false)
const unreadNotifCount = ref(0)

const authLoading = computed(() => false)
const layoutMode = computed(() => settingsStore.layoutMode)
const isDark = computed(() => settingsStore.isDark)
const roleLabel = computed(() => {
  const m: Record<string, string> = { admin: '管理员', user: '用户', guest: '访客' }
  return m[authStore.user?.role || ''] || '用户'
})
const roleTagType = computed(() => {
  const m: Record<string, string> = { admin: 'danger', user: 'success', guest: 'info' }
  return m[authStore.user?.role || ''] || 'info'
})

function toggleTheme() { settingsStore.setThemeMode(settingsStore.isDark ? 'light' : 'dark') }
function toggleLang() { i18nStore.setLocale(i18nStore.locale === 'zh-CN' ? 'en' : 'zh-CN') }
function handleUserCommand(cmd: string) {
  if (cmd === 'logout') { authStore.logout() } else if (cmd === 'settings') { router.push('/settings') }
}

async function fetchUnreadCount() {
  try { const { data } = await api.get('/monitoring/notifications/count'); unreadNotifCount.value = data.count } catch { /* */ }
}

function handleKeydown(e: KeyboardEvent) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') { e.preventDefault(); showCommandPalette.value = !showCommandPalette.value }
  if (e.key === 'Escape') { showCommandPalette.value = false }
}

onMounted(async () => {
  i18nStore.loadLocale()
  await settingsStore.loadSettings()
  if (authStore.isAuthenticated) { await authStore.fetchMe() }
  if (authStore.isAuthenticated) {
    dashboardStore.startTimers()
    dashboardStore.fetchDashboard()
    setInterval(() => { dashboardStore.fetchDashboard(); fetchUnreadCount() }, 30000)
    fetchUnreadCount()
  }
  window.addEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.app-container {
  display: flex;
  min-height: 100vh;
  height: 100vh;
}
.app-container.sidebar {
  padding-left: 260px;
}

.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: 260px;
  z-index: 100;
}

.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  height: 100%;
}

.top-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 20px;
  flex-shrink: 0;
  flex-wrap: nowrap;
  background: var(--bg-glass);
  border-bottom: 1px solid var(--border-color);
  min-height: 52px;
}

.top-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
  white-space: nowrap;
}
.app-title {
  font-size: 18px;
  font-weight: 700;
  background: var(--accent-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.top-center {
  flex: 1;
  min-width: 200px;
  max-width: 500px;
}
.global-search {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--bg-primary);
  border-radius: 10px;
  cursor: pointer;
  border: 1px solid var(--border-color);
  transition: all var(--transition);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.global-search:hover {
  border-color: var(--accent-light);
  box-shadow: var(--shadow-sm);
}
.search-placeholder {
  flex: 1;
  color: var(--text-muted);
  font-size: 14px;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}
kbd {
  background: var(--bg-secondary);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  flex-shrink: 0;
}

.top-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.user-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}
.username {
  font-weight: 500;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.role-tag {
  transform: scale(0.8);
}

.page-content {
  flex: 1;
  padding: 16px 16px 40px;
  overflow-y: auto;
  overflow-x: hidden;
  min-height: 0;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

@media (max-width: 768px) {
  .app-container.sidebar {
    padding-left: 0;
  }
  .sidebar {
    display: none;
  }
  .top-bar {
    margin: 8px 8px 0;
    padding: 8px 12px;
    flex-wrap: wrap;
  }
  .top-center {
    order: 3;
    max-width: 100%;
    margin: 8px 0 0;
    width: 100%;
  }
  .app-title {
    font-size: 15px;
  }
}
</style>
