import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

// Navigation
export const getCategories = () => api.get('/navigation/categories')
export const createCategory = (data: any) => api.post('/navigation/categories', data)
export const updateCategory = (id: number, data: any) => api.put(`/navigation/categories/${id}`, data)
export const deleteCategory = (id: number) => api.delete(`/navigation/categories/${id}`)
export const sortCategories = (items: any[]) => api.put('/navigation/categories/sort', { items })

export const getWebsites = (categoryId?: number) =>
  api.get('/navigation/websites', { params: categoryId !== undefined ? { category_id: categoryId } : {} })
export const createWebsite = (data: any) => api.post('/navigation/websites', data)
export const updateWebsite = (id: number, data: any) => api.put(`/navigation/websites/${id}`, data)
export const deleteWebsite = (id: number) => api.delete(`/navigation/websites/${id}`)
export const sortWebsites = (items: any[]) => api.put('/navigation/websites/sort', { items })
export const recordVisit = (id: number) => api.post(`/navigation/websites/${id}/visit`)
export const getRecentWebsites = (limit = 10) => api.get('/navigation/recent', { params: { limit } })
export const searchNavigation = (q: string) => api.get('/navigation/search', { params: { q } })

// AI Workspace
export const getAIProviders = () => api.get('/workspace/ai-providers')
export const createAIProvider = (data: any) => api.post('/workspace/ai-providers', data)
export const updateAIProvider = (id: number, data: any) => api.put(`/workspace/ai-providers/${id}`, data)
export const deleteAIProvider = (id: number) => api.delete(`/workspace/ai-providers/${id}`)
export const sortAIProviders = (items: any[]) => api.put('/workspace/ai-providers/sort', { items })
export const recordAIVisit = (id: number) => api.post(`/workspace/ai-providers/${id}/visit`)
export const getRecentAI = (limit = 6) => api.get('/workspace/ai-recent', { params: { limit } })

// NAS
export const getNASServices = () => api.get('/workspace/nas-services')
export const createNASService = (data: any) => api.post('/workspace/nas-services', data)
export const updateNASService = (id: number, data: any) => api.put(`/workspace/nas-services/${id}`, data)
export const deleteNASService = (id: number) => api.delete(`/workspace/nas-services/${id}`)
export const sortNASServices = (items: any[]) => api.put('/workspace/nas-services/sort', { items })
export const recordNASVisit = (id: number) => api.post(`/workspace/nas-services/${id}/visit`)

// Docker
export const getContainers = () => api.get('/docker/containers')
export const startContainer = (id: string) => api.post(`/docker/containers/${id}/start`)
export const stopContainer = (id: string) => api.post(`/docker/containers/${id}/stop`)
export const restartContainer = (id: string) => api.post(`/docker/containers/${id}/restart`)
export const getContainerLogs = (id: string, tail = 100) => api.get(`/docker/containers/${id}/logs`, { params: { tail } })

// AI Chat
export const aiChat = (data: any) => api.post('/ai/chat', data)
export const aiCompare = (data: any) => api.post('/ai/compare', data)
export const getChatHistory = () => api.get('/ai/history')
export const createChatHistory = (data: any) => api.post('/ai/history', data)
export const updateChatHistory = (id: number, data: any) => api.put(`/ai/history/${id}`, data)
export const deleteChatHistory = (id: number) => api.delete(`/ai/history/${id}`)

// Prompts
export const getPrompts = (params?: any) => api.get('/prompts', { params })
export const createPrompt = (data: any) => api.post('/prompts', data)
export const updatePrompt = (id: number, data: any) => api.put(`/prompts/${id}`, data)
export const deletePrompt = (id: number) => api.delete(`/prompts/${id}`)
export const recordPromptUse = (id: number) => api.post(`/prompts/${id}/use`)
export const getPromptVersions = (id: number) => api.get(`/prompts/${id}/versions`)
export const getPromptCategories = () => api.get('/prompts/categories')
export const importPrompts = (data: any) => api.post('/prompts/import', data)
export const exportPrompts = () => api.get('/prompts/export')

// Enterprise
export const getEnterpriseSystems = () => api.get('/enterprise')
export const createEnterpriseSystem = (data: any) => api.post('/enterprise', data)
export const updateEnterpriseSystem = (id: number, data: any) => api.put(`/enterprise/${id}`, data)
export const deleteEnterpriseSystem = (id: number) => api.delete(`/enterprise/${id}`)
export const sortEnterpriseSystems = (items: any[]) => api.put('/enterprise/sort', { items })
export const recordEnterpriseVisit = (id: number) => api.post(`/enterprise/${id}/visit`)

// Documents
export const getDocumentSources = () => api.get('/documents/sources')
export const createDocumentSource = (data: any) => api.post('/documents/sources', data)
export const updateDocumentSource = (id: number, data: any) => api.put(`/documents/sources/${id}`, data)
export const deleteDocumentSource = (id: number) => api.delete(`/documents/sources/${id}`)
export const sortDocumentSources = (items: any[]) => api.put('/documents/sources/sort', { items })
export const getSharePointFiles = (sourceId?: number) => api.get('/documents/sharepoint/files', { params: sourceId ? { source_id: sourceId } : {} })
export const syncSharePoint = (sourceId: number) => api.post('/documents/sharepoint/sync', { source_id: sourceId })
export const toggleFileFavorite = (fileId: number) => api.post(`/documents/sharepoint/favorite/${fileId}`)
export const searchSharePoint = (q: string) => api.get('/documents/sharepoint/search', { params: { q } })

// Backgrounds
export const getBackgrounds = () => api.get('/backgrounds')
export const createBackground = (data: FormData) => api.post('/backgrounds', data, { headers: { 'Content-Type': 'multipart/form-data' } })
export const setActiveBackground = (id: number) => api.post(`/backgrounds/set-active/${id}`)
export const deleteBackground = (id: number) => api.delete(`/backgrounds/${id}`)
export const getActiveBackground = () => api.get('/backgrounds/active')

// Dashboard & Data
export const getDashboard = () => api.get('/dashboard')
export const importBookmarks = (content: string, source = 'html') =>
  api.post('/bookmarks/import', { content, source })
export const exportJSON = () => api.get('/export/json', { responseType: 'blob' })
export const importJSON = (data: any) => api.post('/import/json', data)
export const exportExcel = () => api.get('/export/excel', { responseType: 'blob' })
export const autoBackup = () => api.post('/auto-backup')
export const getSetting = (key: string) => api.get(`/settings/${key}`)
export const updateSetting = (key: string, value: string) => api.put(`/settings/${key}`, { value })

// Webhooks
export const getWebhooks = () => api.get('/webhooks')
export const createWebhook = (data: any) => api.post('/webhooks', data)
export const updateWebhook = (id: number, data: any) => api.put(`/webhooks/${id}`, data)
export const deleteWebhook = (id: number) => api.delete(`/webhooks/${id}`)
export const testWebhook = (id: number) => api.post(`/webhooks/${id}/test`)

// Plugins
export const getPlugins = () => api.get('/plugins')
export const togglePlugin = (pluginId: string) => api.put(`/plugins/${pluginId}/toggle`)
export const updatePluginConfig = (pluginId: string, data: any) => api.put(`/plugins/${pluginId}/config`, data)
export const installPlugin = (data: any) => api.post('/plugins', data)
export const uninstallPlugin = (pluginId: string) => api.delete(`/plugins/${pluginId}`)
export const getPluginCategories = () => api.get('/plugins/categories')

// Monitoring
export const getEndpoints = () => api.get('/monitoring/endpoints')
export const createEndpoint = (data: any) => api.post('/monitoring/endpoints', data)
export const updateEndpoint = (id: number, data: any) => api.put(`/monitoring/endpoints/${id}`, data)
export const deleteEndpoint = (id: number) => api.delete(`/monitoring/endpoints/${id}`)
export const checkEndpoint = (id: number) => api.post(`/monitoring/endpoints/${id}/check`)
export const checkAllEndpoints = () => api.post('/monitoring/check-all')

// Notifications
export const getNotifications = (params?: any) => api.get('/monitoring/notifications', { params })
export const markNotificationRead = (id: number) => api.put(`/monitoring/notifications/${id}/read`)
export const markAllNotificationsRead = () => api.put('/monitoring/notifications/read-all')
export const getUnreadNotificationCount = () => api.get('/monitoring/notifications/count')

// Audit
export const getAuditLogs = (params?: any) => api.get('/monitoring/audit-logs', { params })

// GitHub
export const getGitHubConnections = () => api.get('/github/connections')
export const createGitHubConnection = (data: any) => api.post('/github/connections', data)
export const updateGitHubConnection = (id: number, data: any) => api.put(`/github/connections/${id}`, data)
export const deleteGitHubConnection = (id: number) => api.delete(`/github/connections/${id}`)
export const getGitHubItems = (params?: any) => api.get('/github/items', { params })
export const syncGitHub = (id: number) => api.post(`/github/sync/${id}`)

// User Settings
export const getUserSettings = () => api.get('/auth/settings')
export const updateUserSettings = (data: any) => api.put('/auth/settings', data)
export const getI18n = (lang: string) => api.get(`/auth/i18n/${lang}`)

export { api }
export default api
