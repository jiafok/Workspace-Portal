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

      <!-- Account & Users -->
      <div class="setting-card glass">
        <div class="setting-header">
          <el-icon size="20"><UserFilled /></el-icon>
          <span>账户管理</span>
        </div>
        <div class="setting-body">
          <!-- Change password -->
          <h4 style="margin-bottom:12px;font-size:14px">修改密码</h4>
          <el-form :model="pwForm" label-position="top" size="small">
            <el-form-item label="新密码">
              <el-input v-model="pwForm.password" type="password" show-password placeholder="输入新密码" />
            </el-form-item>
            <el-button type="primary" size="small" @click="changePassword">修改密码</el-button>
          </el-form>

          <el-divider />

          <!-- User management -->
          <h4 style="margin-bottom:12px;font-size:14px">用户管理 <el-button text size="small" @click="showAddUser=true"><el-icon><Plus /></el-icon> 添加</el-button></h4>
          <el-table :data="users" size="small" style="width:100%">
            <el-table-column prop="username" label="用户名" />
            <el-table-column prop="role" label="角色" width="80" />
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button text size="small" @click="toggleUserRole(row)" :disabled="row.username==='admin'">切换角色</el-button>
                <el-button text size="small" type="danger" @click="removeUser(row)" :disabled="row.username==='admin'">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
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

    <!-- Add User Dialog -->
    <el-dialog v-model="showAddUser" title="添加用户" width="420px">
      <el-form :model="newUser" label-position="top">
        <el-form-item label="用户名"><el-input v-model="newUser.username" placeholder="username" /></el-form-item>
        <el-form-item label="密码"><el-input v-model="newUser.password" type="password" show-password /></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="newUser.email" /></el-form-item>
        <el-form-item label="显示名"><el-input v-model="newUser.display_name" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="showAddUser=false">取消</el-button><el-button type="primary" @click="addUser">添加</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useSettingsStore } from '../stores/settings'
import { useAuthStore } from '../stores/auth'
import api from '../api'
import { ElMessage } from 'element-plus'

const settingsStore = useSettingsStore()
const authStore = useAuthStore()
const pwForm = reactive({ password: '' })
const users = ref<any[]>([])
const showAddUser = ref(false)
const newUser = reactive({ username: '', password: '', email: '', display_name: '' })

async function fetchUsers() {
  try { const { data } = await api.get('/auth/users'); users.value = data } catch { /* */ }
}

async function changePassword() {
  if (!pwForm.password || pwForm.password.length < 6) { ElMessage.warning('密码至少6位'); return }
  try {
    await api.put(`/auth/users/${authStore.user?.id}/password`, { password: pwForm.password })
    ElMessage.success('密码修改成功')
    pwForm.password = ''
  } catch (e: any) { ElMessage.error(e?.response?.data?.detail || '修改失败') }
}

async function addUser() {
  if (!newUser.username || !newUser.password) { ElMessage.warning('用户名和密码必填'); return }
  try {
    await api.post('/auth/register', { ...newUser })
    ElMessage.success('用户已添加')
    showAddUser.value = false
    newUser.username=''; newUser.password=''; newUser.email=''; newUser.display_name=''
    fetchUsers()
  } catch (e: any) { ElMessage.error(e?.response?.data?.detail || '添加失败') }
}

async function toggleUserRole(row: any) {
  const newRole = row.role === 'admin' ? 'user' : 'admin'
  await api.put(`/auth/users/${row.id}/role`, { role: newRole })
  ElMessage.success(`角色已改为 ${newRole}`)
  fetchUsers()
}

async function removeUser(row: any) {
  // Soft delete: set inactive
  await api.put(`/auth/users/${row.id}/active`, { is_active: false })
  ElMessage.success('用户已禁用')
  fetchUsers()
}

onMounted(fetchUsers)

const features = [
  '导航管理 - 分类/网站的新增、编辑、删除、排序',
  'Web 可视化编辑 - 所有配置在网页完成',
  '自动图标获取 - favicon + 网站标题 + 描述',
  '收藏夹导入 - Chrome/Edge/Firefox HTML 导入',
  'AI 工作区 - 内置9+主流AI，支持置顶/收藏/隐藏',
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
