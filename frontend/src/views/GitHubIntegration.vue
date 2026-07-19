<template>
  <div class="github-page">
    <div class="page-header">
      <h2><el-icon><Connection /></el-icon> 代码平台集成</h2>
      <el-button type="primary" @click="openCreate"><el-icon><Plus /></el-icon> 添加连接</el-button>
    </div>

    <!-- Connections -->
    <div class="connections-row mb-4">
      <div v-for="conn in connections" :key="conn.id" :class="['conn-chip', { active: selectedConn === conn.id }]" @click="selectConn(conn)">
        <span>{{ conn.name }}</span>
        <el-tag size="small">{{ conn.platform === 'github' ? 'GitHub' : 'GitLab' }}</el-tag>
        <el-button text size="small" @click.stop="syncConn(conn)" :loading="syncingId === conn.id"><el-icon><Refresh /></el-icon></el-button>
      </div>
      <el-empty v-if="!connections.length" description="暂无连接，请添加 GitHub/GitLab" :image-size="40" style="padding:8px" />
    </div>

    <!-- PRs & Issues -->
    <div v-if="selectedConn" class="items-section">
      <div class="items-header glass">
        <el-radio-group v-model="itemFilter" size="small">
          <el-radio-button value="all">全部</el-radio-button>
          <el-radio-button value="pr">PR</el-radio-button>
          <el-radio-button value="issue">Issue</el-radio-button>
        </el-radio-group>
        <el-radio-group v-model="stateFilter" size="small">
          <el-radio-button value="all">全部状态</el-radio-button>
          <el-radio-button value="open">Open</el-radio-button>
          <el-radio-button value="closed">Closed</el-radio-button>
        </el-radio-group>
      </div>

      <div v-if="filteredItems.length" class="item-list">
        <div v-for="item in filteredItems" :key="item.id" class="item-card glass glass-hover" @click="openItem(item)">
          <div class="item-left">
            <el-tag :type="item.item_type === 'pr' ? 'primary' : 'warning'" size="small" effect="dark">{{ item.item_type === 'pr' ? 'PR' : 'ISSUE' }}</el-tag>
            <span class="item-title">{{ item.title }}</span>
          </div>
          <div class="item-right">
            <span class="item-repo">{{ item.repo_name }}</span>
            <span class="item-author">@{{ item.author }}</span>
            <el-tag :type="item.state === 'open' ? 'success' : item.state === 'merged' ? 'info' : ''" size="small">{{ item.state }}</el-tag>
          </div>
        </div>
      </div>
      <el-empty v-else description="暂无数据，请同步" />
    </div>

    <el-dialog v-model="showDialog" :title="editing ? '编辑连接' : '添加连接'" width="520px">
      <el-form :model="form" label-position="top">
        <el-form-item label="名称 *"><el-input v-model="form.name" placeholder="如: 工作 GitHub" /></el-form-item>
        <el-form-item label="平台"><el-select v-model="form.platform" style="width:100%"><el-option value="github" label="GitHub" /><el-option value="gitlab" label="GitLab" /></el-select></el-form-item>
        <el-form-item label="API URL"><el-input v-model="form.base_url" placeholder="https://api.github.com" /></el-form-item>
        <el-form-item label="API Token *"><el-input v-model="form.api_token" type="password" show-password placeholder="ghp_xxx 或 glpat-xxx" /></el-form-item>
        <el-form-item label="用户名"><el-input v-model="form.username" /></el-form-item>
        <el-form-item label="仓库列表 (JSON数组)"><el-input v-model="form.repos" placeholder='["owner/repo1","owner/repo2"]' /></el-form-item>
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="同步 PR"><el-switch v-model="form.sync_pull_requests" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="同步 Issue"><el-switch v-model="form.sync_issues" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="启用"><el-switch v-model="form.is_enabled" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="showDialog = false">取消</el-button><el-button type="primary" @click="handleSave">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import api from '../api'
import { ElMessage } from 'element-plus'

const connections = ref<any[]>([])
const items = ref<any[]>([])
const selectedConn = ref<number | null>(null)
const itemFilter = ref('all')
const stateFilter = ref('all')
const syncingId = ref<number | null>(null)
const showDialog = ref(false)
const editing = ref<any>(null)
const form = reactive({ name: '', platform: 'github', base_url: 'https://api.github.com', api_token: '', username: '', repos: '[]', sync_pull_requests: true, sync_issues: true, is_enabled: true })

const filteredItems = computed(() => {
  let result = items.value
  if (itemFilter.value !== 'all') result = result.filter(i => i.item_type === itemFilter.value)
  if (stateFilter.value !== 'all') result = result.filter(i => i.state === stateFilter.value)
  return result
})

async function fetchConnections() { const { data } = await api.get('/github/connections'); connections.value = data }
async function selectConn(conn: any) { selectedConn.value = conn.id; const { data } = await api.get('/github/items', { params: { connection_id: conn.id } }); items.value = data }
async function syncConn(conn: any) { syncingId.value = conn.id; await api.post(`/github/sync/${conn.id}`); syncingId.value = null; ElMessage.success('同步完成'); selectConn(conn) }
function openItem(item: any) { if (item.url) window.open(item.url, '_blank') }

function openCreate() { editing.value = null; form.name = ''; form.api_token = ''; form.repos = '[]'; showDialog.value = true }
function openEdit(conn: any) { editing.value = conn; Object.assign(form, conn); showDialog.value = true }
async function handleSave() {
  if (!form.name || !form.api_token) return
  if (editing.value) { await api.put(`/github/connections/${editing.value.id}`, { ...form }); ElMessage.success('已更新') }
  else { await api.post('/github/connections', { ...form }); ElMessage.success('已添加') }
  showDialog.value = false; fetchConnections()
}

onMounted(fetchConnections)
</script>

<style scoped>
.github-page { max-width: 1100px; margin: 0 auto; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.page-header h2 { display: flex; align-items: center; gap: 8px; font-size: 22px; font-weight: 800; }
.connections-row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.conn-chip { display: flex; align-items: center; gap: 6px; padding: 8px 14px; border-radius: 10px; cursor: pointer; border: 1px solid var(--border-color); transition: all var(--transition); }
.conn-chip.active { background: var(--accent); color: white; border-color: var(--accent); }
.items-header { display: flex; gap: 12px; padding: 10px 16px; margin-bottom: 10px; }
.item-list { display: flex; flex-direction: column; gap: 4px; }
.item-card { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; cursor: pointer; }
.item-left { display: flex; align-items: center; gap: 10px; flex: 1; min-width: 0; }
.item-title { font-size: 14px; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.item-right { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }
.item-repo { font-size: 12px; color: var(--text-muted); }
.item-author { font-size: 12px; color: var(--text-muted); }
</style>
