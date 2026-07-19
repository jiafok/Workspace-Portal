import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api'

const zhCN = {
  nav: { home: '工作台首页', ai_chat: 'AI 对话', ai_compare: '多模型对比', ai: 'AI 工具', prompts: 'Prompt 中心', navigate: '导航管理', enterprise: '企业系统', documents: '文档中心', nas: 'NAS 中心', docker: 'Docker 监控', data: '数据管理', personalize: '个性化', settings: '系统设置', plugins: '插件市场', monitoring: '系统监控', github: '代码平台', webhooks: 'Webhook', audit: '审计日志', },
  search: '搜索网站、分类、AI、文档...',
  hotkey: 'Ctrl+K',
  welcome: { morning: '早上好', afternoon: '下午好', evening: '晚上好' },
  common: { save: '保存', cancel: '取消', delete: '删除', edit: '编辑', add: '新增', search: '搜索', refresh: '刷新', export: '导出', import: '导入', enable: '启用', disable: '禁用', confirm: '确认', yes: '是', no: '否', loading: '加载中...', noData: '暂无数据', success: '操作成功', failed: '操作失败', },
  theme: { dark: '深色模式', light: '浅色模式', auto: '自动' },
  layout: { card: '卡片', list: '列表', desktop: '桌面', sidebar: '侧边栏' },
}

const en = {
  nav: { home: 'Dashboard', ai_chat: 'AI Chat', ai_compare: 'AI Compare', ai: 'AI Tools', prompts: 'Prompts', navigate: 'Navigation', enterprise: 'Enterprise', documents: 'Documents', nas: 'NAS Center', docker: 'Docker Monitor', data: 'Data', personalize: 'Personalize', settings: 'Settings', plugins: 'Plugin Market', monitoring: 'Monitoring', github: 'Code Platform', webhooks: 'Webhooks', audit: 'Audit Log', },
  search: 'Search sites, categories, AI, docs...',
  hotkey: 'Ctrl+K',
  welcome: { morning: 'Good Morning', afternoon: 'Good Afternoon', evening: 'Good Evening' },
  common: { save: 'Save', cancel: 'Cancel', delete: 'Delete', edit: 'Edit', add: 'Add', search: 'Search', refresh: 'Refresh', export: 'Export', import: 'Import', enable: 'Enable', disable: 'Disable', confirm: 'Confirm', yes: 'Yes', no: 'No', loading: 'Loading...', noData: 'No data', success: 'Success', failed: 'Failed', },
  theme: { dark: 'Dark', light: 'Light', auto: 'Auto' },
  layout: { card: 'Card', list: 'List', desktop: 'Desktop', sidebar: 'Sidebar' },
}

export const useI18nStore = defineStore('i18n', () => {
  const locale = ref('zh-CN')
  const t = computed(() => locale.value === 'zh-CN' ? zhCN : en)

  function setLocale(lang: string) {
    locale.value = lang
    localStorage.setItem('wp_lang', lang)
  }

  function loadLocale() {
    const saved = localStorage.getItem('wp_lang')
    if (saved === 'en' || saved === 'zh-CN') locale.value = saved
  }

  return { locale, t, setLocale, loadLocale }
})
