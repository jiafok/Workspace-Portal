<template>
  <div class="dashboard-strip glass">
    <div class="dash-item time-item">
      <el-icon><Clock /></el-icon>
      <span>{{ dashboardStore.currentTime }}</span>
    </div>
    <div class="dash-item">
      <el-icon><Odometer /></el-icon>
      <span>CPU {{ dashboardStore.systemInfo.cpu_percent }}%</span>
    </div>
    <div class="dash-item">
      <el-icon><Monitor /></el-icon>
      <span>MEM {{ dashboardStore.systemInfo.memory_percent }}%</span>
    </div>
    <div class="dash-item">
      <el-icon><FolderOpened /></el-icon>
      <span>DISK {{ dashboardStore.systemInfo.disk_percent }}%</span>
    </div>
    <div class="dash-item stats-item">
      <span class="stat-badge">{{ dashboardStore.stats.total_websites }} 网站</span>
      <span class="stat-badge">{{ dashboardStore.stats.total_ai }} AI</span>
      <span class="stat-badge">{{ dashboardStore.stats.total_nas }} NAS</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useDashboardStore } from '../stores/dashboard'
const dashboardStore = useDashboardStore()
</script>

<style scoped>
.dashboard-strip {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 10px 20px;
  margin: 10px 16px 0;
  flex-wrap: wrap;
}
.dash-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-secondary);
  font-variant-numeric: tabular-nums;
}
.time-item {
  font-weight: 600;
  color: var(--text-primary);
}
.stats-item {
  margin-left: auto;
  gap: 8px;
}
.stat-badge {
  background: var(--accent);
  color: white;
  padding: 2px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 500;
}
@media (max-width: 768px) {
  .dashboard-strip {
    gap: 10px;
    padding: 8px 12px;
    margin: 8px 8px 0;
  }
  .dash-item {
    font-size: 12px;
  }
  .stats-item {
    margin-left: 0;
    width: 100%;
    justify-content: flex-start;
  }
}
</style>
