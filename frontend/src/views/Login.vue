<template>
  <div class="login-page">
    <div class="login-card glass">
      <div class="login-header">
        <h1>🚀 Workspace Portal</h1>
        <p class="subtitle">Engineer Workspace Center</p>
      </div>

      <el-form :model="form" @submit.prevent="handleLogin" label-position="top" size="large">
        <el-form-item label="用户名">
          <el-input v-model="form.username" placeholder="admin / demo / guest" prefix-icon="User" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" show-password placeholder="admin123 / demo123" prefix-icon="Lock" @keyup.enter="handleLogin" />
        </el-form-item>
        <el-button type="primary" native-type="submit" :loading="loading" class="w-full" size="large">
          登录
        </el-button>
      </el-form>

      <el-divider>或</el-divider>

      <!-- OAuth buttons -->
      <div class="oauth-buttons">
        <el-button class="w-full mb-2" @click="oauthLogin('azure_ad')" :disabled="!oauthEnabled.azure_ad">
          <el-icon><Platform /></el-icon> Microsoft Entra ID / Azure AD
        </el-button>
        <el-button class="w-full" @click="oauthLogin('oidc')" :disabled="!oauthEnabled.oidc">
          <el-icon><Link /></el-icon> OIDC / OAuth2
        </el-button>
      </div>

      <div class="demo-hint">
        <p>演示账号: <b>admin</b> / <b>admin123</b> (管理员)</p>
        <p>演示账号: <b>demo</b> / <b>demo123</b> (普通用户)</p>
        <p>访客账号: <b>guest</b> (免密)</p>
      </div>

      <el-alert v-if="error" :title="error" type="error" show-icon closable @close="error = ''" class="mt-4" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import api from '../api'

const router = useRouter()
const authStore = useAuthStore()
const form = reactive({ username: 'admin', password: 'admin123' })
const loading = ref(false)
const error = ref('')
const oauthEnabled = reactive({ azure_ad: false, oidc: false })

async function handleLogin() {
  if (!form.username || !form.password) return
  loading.value = true; error.value = ''
  try {
    const { data } = await api.post('/auth/login', {
      username: form.username, password: form.password
    })
    authStore.setAuth(data.access_token, data.user)
    router.push('/')
  } catch (e: any) {
    error.value = e?.response?.data?.detail || '登录失败'
  }
  loading.value = false
}

function oauthLogin(provider: string) {
  // Redirect to OAuth provider
  window.location.href = `/api/auth/oauth/login/${provider}`
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #6c5ce7 100%);
}
.login-card {
  width: 420px;
  padding: 40px;
  max-width: 95vw;
}
.login-header {
  text-align: center;
  margin-bottom: 28px;
}
.login-header h1 {
  font-size: 26px;
  font-weight: 800;
  background: var(--accent-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.subtitle {
  color: var(--text-secondary);
  font-size: 13px;
  margin-top: 4px;
}
.oauth-buttons {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.demo-hint {
  margin-top: 20px;
  font-size: 12px;
  color: var(--text-muted);
  text-align: center;
}
.demo-hint p {
  margin: 2px 0;
}
.demo-hint b {
  color: var(--accent-light);
}
</style>
