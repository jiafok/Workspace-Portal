<template>
  <div class="data-management">
    <div class="page-header">
      <h2><el-icon><FolderOpened /></el-icon> 数据管理</h2>
    </div>

    <div class="data-grid">
      <!-- Export -->
      <div class="data-card glass">
        <el-icon size="32" color="var(--accent)"><Download /></el-icon>
        <h3>导出配置</h3>
        <p>将全部导航数据导出备份</p>
        <div class="card-btns">
          <el-button @click="doExport('json')">
            <el-icon><Document /></el-icon> JSON
          </el-button>
          <el-button @click="doExport('excel')">
            <el-icon><Grid /></el-icon> CSV
          </el-button>
        </div>
      </div>

      <!-- Import -->
      <div class="data-card glass">
        <el-icon size="32" color="#00b894"><Upload /></el-icon>
        <h3>导入配置</h3>
        <p>从 JSON 文件恢复数据</p>
        <div class="card-btns">
          <el-upload
            :auto-upload="false"
            :show-file-list="false"
            accept=".json"
            :on-change="handleImportFile"
          >
            <el-button>
              <el-icon><Document /></el-icon> 选择 JSON 文件
            </el-button>
          </el-upload>
        </div>
      </div>

      <!-- Auto Backup -->
      <div class="data-card glass">
        <el-icon size="32" color="#fdcb6e"><Timer /></el-icon>
        <h3>自动备份</h3>
        <p>立即执行一次自动备份</p>
        <div class="card-btns">
          <el-button @click="doBackup" :loading="backupLoading">
            <el-icon><Clock /></el-icon> 立即备份
          </el-button>
        </div>
      </div>

      <!-- Import Bookmarks -->
      <div class="data-card glass">
        <el-icon size="32" color="#e17055"><Collection /></el-icon>
        <h3>导入收藏夹</h3>
        <p>从浏览器导入 HTML 收藏夹</p>
        <BookmarkImport @done="onBookmarkImport" />
      </div>
    </div>

    <!-- Stats -->
    <div class="data-stats glass" style="margin-top:24px; padding:20px">
      <h3 style="margin-bottom:16px">数据统计</h3>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="网站总数">{{ stats.total_websites }}</el-descriptions-item>
        <el-descriptions-item label="分类总数">{{ stats.total_categories }}</el-descriptions-item>
        <el-descriptions-item label="AI 工具">{{ stats.total_ai }}</el-descriptions-item>
        <el-descriptions-item label="NAS 服务">{{ stats.total_nas }}</el-descriptions-item>
      </el-descriptions>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { exportJSON, exportExcel, importJSON, autoBackup, getDashboard } from '../api'
import BookmarkImport from '../components/BookmarkImport.vue'
import { ElMessage } from 'element-plus'

const backupLoading = ref(false)
const stats = ref({ total_websites: 0, total_categories: 0, total_ai: 0, total_nas: 0 })

async function doExport(type: string) {
  try {
    const { data } = type === 'json' ? await exportJSON() : await exportExcel()
    const blob = new Blob([data], { type: type === 'json' ? 'application/json' : 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `workspace_export.${type === 'json' ? 'json' : 'csv'}`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch {
    ElMessage.error('导出失败')
  }
}

async function handleImportFile(file: any) {
  try {
    const text = await file.raw.text()
    const data = JSON.parse(text)
    await importJSON(data)
    ElMessage.success('导入成功，请刷新页面查看')
    setTimeout(() => location.reload(), 1000)
  } catch {
    ElMessage.error('导入失败，请检查文件格式')
  }
}

async function doBackup() {
  backupLoading.value = true
  try {
    await autoBackup()
    ElMessage.success('备份完成')
  } catch {
    ElMessage.error('备份失败')
  }
  backupLoading.value = false
}

function onBookmarkImport() {
  ElMessage.success('收藏夹导入成功')
  fetchStats()
}

async function fetchStats() {
  try {
    const { data } = await getDashboard()
    stats.value = data.stats
  } catch { /* ignore */ }
}

onMounted(fetchStats)
</script>

<style scoped>
.data-management {
  max-width: 1100px;
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
.data-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}
.data-card {
  padding: 24px;
  text-align: center;
}
.data-card h3 {
  margin: 12px 0 6px;
  font-size: 17px;
  font-weight: 700;
}
.data-card p {
  color: var(--text-secondary);
  font-size: 13px;
  margin-bottom: 16px;
}
.card-btns {
  display: flex;
  gap: 8px;
  justify-content: center;
}

@media (max-width: 768px) {
  .data-grid {
    grid-template-columns: 1fr;
  }
}
</style>
