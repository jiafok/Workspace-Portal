import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: () => import('../views/Home.vue') },
    { path: '/login', name: 'login', component: () => import('../views/Login.vue') },
    { path: '/navigate', name: 'navigate', component: () => import('../views/NavigationManager.vue') },
    { path: '/ai', name: 'ai', component: () => import('../views/AIWorkspace.vue') },
    { path: '/ai-chat', name: 'aiChat', component: () => import('../views/AIChat.vue') },
    { path: '/ai-compare', name: 'aiCompare', component: () => import('../views/AICompare.vue') },
    { path: '/prompts', name: 'prompts', component: () => import('../views/PromptManager.vue') },
    { path: '/enterprise', name: 'enterprise', component: () => import('../views/EnterpriseSystems.vue') },
    { path: '/documents', name: 'documents', component: () => import('../views/DocumentCenter.vue') },
    { path: '/nas', name: 'nas', component: () => import('../views/NASCenter.vue') },
    { path: '/docker', name: 'docker', component: () => import('../views/DockerMonitor.vue') },
    { path: '/data', name: 'data', component: () => import('../views/DataManagement.vue') },
    { path: '/settings', name: 'settings', component: () => import('../views/Settings.vue') },
    { path: '/personalize', name: 'personalize', component: () => import('../views/Personalization.vue') },
    { path: '/plugins', name: 'plugins', component: () => import('../views/PluginMarket.vue') },
    { path: '/monitoring', name: 'monitoring', component: () => import('../views/EndpointMonitor.vue') },
    { path: '/notifications', name: 'notifications', component: () => import('../views/NotificationCenter.vue') },
    { path: '/github', name: 'github', component: () => import('../views/GitHubIntegration.vue') },
    { path: '/webhooks', name: 'webhooks', component: () => import('../views/WebhookManager.vue') },
    { path: '/audit', name: 'audit', component: () => import('../views/AuditLogView.vue') },
  ],
})

router.beforeEach((to, _from, next) => {
  // Allow login page always
  if (to.path === '/login') return next()

  const authStore = useAuthStore()
  if (!authStore.isAuthenticated) return next()

  // Admin sees everything
  if (authStore.user?.role === 'admin') return next()

  // Non-admin: check page visibility
  const visible = authStore.visiblePages
  const pages = (visible && visible.length) ? visible : ['/', '/ai-chat', '/navigate', '/enterprise', '/documents', '/personalize', '/settings']

  if (pages.includes(to.path) || to.path === '/') return next()

  // Redirect blocked pages to home
  return next('/')
})

export default router
