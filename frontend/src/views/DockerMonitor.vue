<template>
  <div class="docker-monitor">
    <div class="page-header">
      <h2><el-icon><Odometer /></el-icon> Docker 监控</h2>
      <el-button @click="fetchContainers" :loading="loading">
        <el-icon><Refresh /></el-icon> 刷新
      </el-button>
    </div>

    <div v-if="!dockerAvailable" class="notice glass">
      <el-icon size="24"><WarningFilled /></el-icon>
      <span>Docker socket 不可用。请确保 /var/run/docker.sock 已挂载。</span>
    </div>

    <div v-loading="loading" class="container-list">
      <div v-for="c in containers" :key="c.container_id" class="container-card glass">
        <div class="container-top">
          <div class="container-main">
            <span :class="['status-dot', c.status === 'running' ? 'running' : 'stopped']"></span>
            <span class="container-name">{{ c.name }}</span>
            <el-tag :type="c.status === 'running' ? 'success' : 'info'" size="small">
              {{ c.status === 'running' ? '运行中' : c.status }}
            </el-tag>
          </div>
          <div class="container-controls" v-if="c.status === 'running'">
            <el-button size="small" @click="doAction(c, 'stop')">
              <el-icon><VideoPause /></el-icon>
            </el-button>
            <el-button size="small" @click="doAction(c, 'restart')">
              <el-icon><Refresh /></el-icon>
            </el-button>
          </div>
          <div class="container-controls" v-else>
            <el-button size="small" type="primary" @click="doAction(c, 'start')">
              <el-icon><VideoPlay /></el-icon> 启动
            </el-button>
          </div>
        </div>
        <div class="container-details">
          <div class="detail-item">
            <span class="detail-label">镜像</span>
            <span class="detail-value">{{ c.image }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">CPU</span>
            <span class="detail-value">{{ c.cpu_percent }}%</span>
            <el-progress :percentage="Math.min(c.cpu_percent, 100)" :stroke-width="4" :show-text="false" style="width:60px" />
          </div>
          <div class="detail-item">
            <span class="detail-label">内存</span>
            <span class="detail-value">{{ c.memory_usage }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">运行时间</span>
            <span class="detail-value">{{ c.uptime }}</span>
          </div>
        </div>
      </div>
    </div>

    <el-empty v-if="!loading && !containers.length && dockerAvailable" description="未发现容器" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getContainers, startContainer, stopContainer, restartContainer } from '../api'
import { ElMessage } from 'element-plus'

const containers = ref<any[]>([])
const loading = ref(false)
const dockerAvailable = ref(true)

async function fetchContainers() {
  loading.value = true
  try {
    const { data } = await getContainers()
    containers.value = data
    dockerAvailable.value = true
  } catch {
    dockerAvailable.value = false
  }
  loading.value = false
}

async function doAction(c: any, action: string) {
  try {
    if (action === 'start') await startContainer(c.container_id)
    else if (action === 'stop') await stopContainer(c.container_id)
    else if (action === 'restart') await restartContainer(c.container_id)
    ElMessage.success(`容器 ${action === 'start' ? '启动' : action === 'stop' ? '停止' : '重启'} 成功`)
    await fetchContainers()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.error || '操作失败')
  }
}

onMounted(fetchContainers)
</script>

<style scoped>
.docker-monitor {
  max-width: 1000px;
  margin: 0 auto;
}
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.page-header h2 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 22px;
  font-weight: 800;
}
.notice {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px;
  margin-bottom: 20px;
  color: var(--text-secondary);
}
.container-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.container-card {
  padding: 18px 20px;
}
.container-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.container-main {
  display: flex;
  align-items: center;
  gap: 10px;
}
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.status-dot.running {
  background: #00b894;
  box-shadow: 0 0 8px rgba(0, 184, 148, 0.5);
}
.status-dot.stopped {
  background: #b2bec3;
}
.container-name {
  font-size: 16px;
  font-weight: 600;
}
.container-controls {
  display: flex;
  gap: 6px;
}
.container-details {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}
.detail-item {
  display: flex;
  align-items: center;
  gap: 6px;
}
.detail-label {
  font-size: 12px;
  color: var(--text-muted);
}
.detail-value {
  font-size: 13px;
  font-weight: 500;
}
</style>
