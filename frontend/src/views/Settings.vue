<template>
  <div class="settings-page">
    <div class="page-header">
      <h2><el-icon><Setting /></el-icon> 系统设置</h2>
    </div>

    <div class="settings-grid">
      <!-- Layout -->
      <div class="setting-card glass">
        <div class="setting-header">
          <el-icon size="20"><Platform /></el-icon>
          <span>布局模式</span>
        </div>
        <div class="setting-body">
          <el-radio-group v-model="settingsStore.layoutMode" @change="(v: string) => settingsStore.setLayoutMode(v as any)">
            <el-radio-button value="card">卡片</el-radio-button>
            <el-radio-button value="list">列表</el-radio-button>
            <el-radio-button value="desktop">桌面</el-radio-button>
            <el-radio-button value="sidebar">侧边栏</el-radio-button>
          </el-radio-group>
        </div>
      </div>

      <!-- Theme -->
      <div class="setting-card glass">
        <div class="setting-header">
          <el-icon size="20"><Brush /></el-icon>
          <span>主题模式</span>
        </div>
        <div class="setting-body">
          <el-radio-group v-model="settingsStore.themeMode" @change="(v: string) => settingsStore.setThemeMode(v as any)">
            <el-radio-button value="light">
              <el-icon><Sunny /></el-icon> 浅色
            </el-radio-button>
            <el-radio-button value="dark">
              <el-icon><Moon /></el-icon> 深色
            </el-radio-button>
            <el-radio-button value="auto">
              <el-icon><Setting /></el-icon> 自动
            </el-radio-button>
          </el-radio-group>
        </div>
      </div>

      <!-- About -->
      <div class="setting-card glass">
        <div class="setting-header">
          <el-icon size="20"><InfoFilled /></el-icon>
          <span>关于</span>
        </div>
        <div class="setting-body">
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="产品">Workspace Portal</el-descriptions-item>
            <el-descriptions-item label="版本">1.0.0</el-descriptions-item>
            <el-descriptions-item label="前端">Vue 3 + Element Plus + Pinia + Vite</el-descriptions-item>
            <el-descriptions-item label="后端">Python FastAPI</el-descriptions-item>
            <el-descriptions-item label="数据库">SQLite</el-descriptions-item>
            <el-descriptions-item label="部署">Docker / 群晖 DSM / Linux / Windows</el-descriptions-item>
          </el-descriptions>
        </div>
      </div>

      <!-- Features -->
      <div class="setting-card glass">
        <div class="setting-header">
          <el-icon size="20"><MagicStick /></el-icon>
          <span>功能特性</span>
        </div>
        <div class="setting-body feature-list">
          <div v-for="f in features" :key="f" class="feature-item">
            <el-icon color="#00b894"><Check /></el-icon>
            <span>{{ f }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useSettingsStore } from '../stores/settings'

const settingsStore = useSettingsStore()

const features = [
  '导航管理 - 分类/网站的新增、编辑、删除、拖拽排序',
  'Web 可视化编辑 - 所有配置在网页完成',
  '拖拽排序 - 网站卡片/分类拖拽排序、跨分类移动',
  '自动图标获取 - favicon + 网站标题 + 描述',
  '收藏夹导入 - Chrome/Edge/Firefox HTML 导入',
  'AI 工作区 - 内置8+主流AI，支持置顶/收藏/隐藏',
  'NAS 中心 - 内网/远程地址自动切换',
  'Docker 监控 - 容器状态/CPU/内存/启停控制',
  '全局搜索 - Ctrl+K 快速搜索',
  '多布局模式 - 卡片/列表/桌面/侧边栏',
  '深色/浅色/自动主题',
  '仪表盘 - 系统资源/时间/最近访问',
  '数据管理 - JSON/CSV 导入导出、自动备份',
]
</script>

<style scoped>
.settings-page {
  max-width: 900px;
  margin: 0 auto;
}
.page-header {
  margin-bottom: 24px;
}
.page-header h2 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 22px;
  font-weight: 800;
}
.settings-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.setting-card {
  padding: 20px;
}
.setting-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 16px;
}
.setting-body {
  padding-left: 4px;
}
.feature-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.feature-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text-secondary);
}

@media (max-width: 768px) {
  .settings-grid {
    grid-template-columns: 1fr;
  }
}
</style>
