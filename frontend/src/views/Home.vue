<template>
  <div class="home-page">
    <!-- Welcome -->
    <div class="welcome-section animate-in">
      <h2 class="welcome-title">
        下午好 👋
      </h2>
      <p class="welcome-sub">{{ dashboardStore.currentTime }}</p>
    </div>

    <!-- Quick Stats -->
    <div class="quick-stats">
      <div v-for="(stat, i) in statCards" :key="i" class="stat-card glass animate-in" :style="{ animationDelay: i * 0.05 + 's' }">
        <div class="stat-icon" :style="{ background: stat.color }">
          <el-icon size="22"><component :is="stat.icon" /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ stat.value }}</span>
          <span class="stat-label">{{ stat.label }}</span>
        </div>
      </div>
    </div>

    <div class="home-grid">
      <!-- Recent Websites -->
      <div class="home-section glass animate-in">
        <h3 class="section-title">
          <el-icon><Timer /></el-icon> 最近访问
        </h3>
        <div class="recent-list" v-if="dashboardStore.recentWebsites.length">
          <div
            v-for="web in dashboardStore.recentWebsites.slice(0, 8)"
            :key="web.id"
            class="recent-item"
            @click="openSite(web)"
          >
            <div class="mini-icon">
              <img v-if="web.icon_url" :src="web.icon_url" @error="e => (e.target as any).style.display = 'none'" />
              <el-icon v-else size="14"><Link /></el-icon>
            </div>
            <span class="recent-name">{{ web.name }}</span>
            <span class="recent-time">{{ timeAgo(web.last_visited) }}</span>
          </div>
        </div>
        <el-empty v-else description="暂无访问记录" :image-size="60" />
      </div>

      <!-- Quick AI -->
      <div class="home-section glass animate-in">
        <h3 class="section-title">
          <el-icon><MagicStick /></el-icon> 快捷 AI
        </h3>
        <div class="ai-grid" v-if="dashboardStore.recentAI.length">
          <div
            v-for="ai in dashboardStore.recentAI.slice(0, 6)"
            :key="ai.id"
            class="ai-chip"
            @click="openAI(ai)"
          >
            {{ ai.name }}
          </div>
        </div>
        <el-empty v-else description="暂无 AI 记录" :image-size="60" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useDashboardStore } from '../stores/dashboard'
import { useNavigationStore } from '../stores/navigation'
import { recordVisit as recordVisitApi, recordAIVisit } from '../api'

const dashboardStore = useDashboardStore()
const navigationStore = useNavigationStore()

const statCards = computed(() => [
  { icon: 'Connection', value: dashboardStore.stats.total_websites, label: '网站', color: 'linear-gradient(135deg, #6c5ce7, #a29bfe)' },
  { icon: 'FolderOpened', value: dashboardStore.stats.total_categories, label: '分类', color: 'linear-gradient(135deg, #00b894, #55efc4)' },
  { icon: 'MagicStick', value: dashboardStore.stats.total_ai, label: 'AI 工具', color: 'linear-gradient(135deg, #fdcb6e, #ffeaa7)' },
  { icon: 'Monitor', value: dashboardStore.stats.total_nas, label: 'NAS 服务', color: 'linear-gradient(135deg, #e17055, #fab1a0)' },
])

function openSite(web: any) {
  recordVisitApi(web.id)
  window.open(web.url, '_blank')
}

function openAI(ai: any) {
  recordAIVisit(ai.id)
  window.open(ai.url, '_blank')
}

function timeAgo(date: string | null) {
  if (!date) return ''
  const d = new Date(date)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return '刚刚'
  if (mins < 60) return `${mins}分钟前`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}小时前`
  return `${Math.floor(hours / 24)}天前`
}

onMounted(() => {
  dashboardStore.fetchDashboard()
})
</script>

<style scoped>
.home-page {
  max-width: 1200px;
  margin: 0 auto;
}

.welcome-section {
  padding: 8px 0 20px;
}
.welcome-title {
  font-size: 28px;
  font-weight: 800;
  margin-bottom: 4px;
}
.welcome-sub {
  color: var(--text-secondary);
  font-size: 14px;
}

.quick-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 24px;
}
.stat-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 18px;
}
.stat-icon {
  width: 46px;
  height: 46px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}
.stat-info {
  display: flex;
  flex-direction: column;
}
.stat-value {
  font-size: 24px;
  font-weight: 800;
}
.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.home-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.home-section {
  padding: 20px;
}
.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 16px;
}

.recent-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.recent-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: all var(--transition);
}
.recent-item:hover {
  background: var(--bg-primary);
}
.mini-icon {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent-gradient);
  color: white;
  flex-shrink: 0;
}
.mini-icon img {
  width: 16px;
  height: 16px;
  border-radius: 3px;
}
.recent-name {
  flex: 1;
  font-size: 13px;
  font-weight: 500;
}
.recent-time {
  font-size: 11px;
  color: var(--text-muted);
}

.ai-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}
.ai-chip {
  padding: 10px 14px;
  background: var(--bg-primary);
  border-radius: 10px;
  text-align: center;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all var(--transition);
}
.ai-chip:hover {
  background: var(--accent);
  color: white;
}

@media (max-width: 768px) {
  .quick-stats {
    grid-template-columns: repeat(2, 1fr);
  }
  .home-grid {
    grid-template-columns: 1fr;
  }
  .ai-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .welcome-title {
    font-size: 22px;
  }
}
</style>
