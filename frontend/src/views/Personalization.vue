<template>
  <div class="personalization">
    <div class="page-header">
      <h2><el-icon><Brush /></el-icon> 个性化设置</h2>
    </div>

    <div class="settings-grid">
      <!-- Background Type -->
      <div class="setting-card glass">
        <h3>背景类型</h3>
        <el-radio-group v-model="activeBgType" @change="applyBg">
          <el-radio-button value="color">纯色</el-radio-button>
          <el-radio-button value="gradient">渐变</el-radio-button>
          <el-radio-button value="image">图片</el-radio-button>
          <el-radio-button value="dynamic">动态</el-radio-button>
        </el-radio-group>

        <!-- Color picker -->
        <div v-if="activeBgType === 'color'" class="mt-4">
          <el-color-picker v-model="bgColor" show-alpha @change="applyBg" />
          <span class="ml-2 text-sm text-secondary">选择背景颜色</span>
        </div>

        <!-- Gradient -->
        <div v-if="activeBgType === 'gradient'" class="mt-4">
          <div class="gradient-presets">
            <div v-for="(g, i) in gradients" :key="i" :class="['gradient-block', { active: bgValue === g.value }]"
              :style="{ background: g.value }" @click="bgValue = g.value; applyBg()" />
          </div>
        </div>

        <!-- Image Upload -->
        <div v-if="activeBgType === 'image'" class="mt-4">
          <el-upload :auto-upload="false" :show-file-list="false" accept="image/*" :on-change="handleImageUpload" drag>
            <div class="upload-area">
              <el-icon size="32"><UploadFilled /></el-icon>
              <p>点击或拖拽上传壁纸</p>
            </div>
          </el-upload>
          <div v-if="uploadedImages.length" class="image-grid mt-3">
            <div v-for="(img, i) in uploadedImages" :key="i" :class="['img-thumb', { active: bgValue === img }]"
              :style="{ backgroundImage: `url(${img})` }" @click="bgValue = img; applyBg()" />
          </div>
        </div>
      </div>

      <!-- Layout -->
      <div class="setting-card glass">
        <h3>布局模式</h3>
        <el-radio-group v-model="settingsStore.layoutMode" @change="(v: string) => settingsStore.setLayoutMode(v as any)">
          <el-radio-button value="card">卡片</el-radio-button>
          <el-radio-button value="list">列表</el-radio-button>
          <el-radio-button value="desktop">桌面</el-radio-button>
          <el-radio-button value="sidebar">侧边栏</el-radio-button>
        </el-radio-group>
      </div>

      <!-- Theme -->
      <div class="setting-card glass">
        <h3>主题</h3>
        <el-radio-group v-model="settingsStore.themeMode" @change="(v: string) => settingsStore.setThemeMode(v as any)">
          <el-radio-button value="dark"><el-icon><Moon /></el-icon> 深色</el-radio-button>
          <el-radio-button value="light"><el-icon><Sunny /></el-icon> 浅色</el-radio-button>
          <el-radio-button value="auto"><el-icon><Setting /></el-icon> 自动</el-radio-button>
        </el-radio-group>
      </div>

      <!-- Accent Color -->
      <div class="setting-card glass">
        <h3>主题色</h3>
        <div class="accent-colors">
          <div v-for="c in accentColors" :key="c" :class="['accent-dot', { active: currentAccent === c }]"
            :style="{ background: c }" @click="setAccent(c)" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useSettingsStore } from '../stores/settings'
import { getActiveBackground, createBackground, setActiveBackground } from '../api'
import { ElMessage } from 'element-plus'

const settingsStore = useSettingsStore()

const activeBgType = ref('color')
const bgColor = ref('#0f0f1a')
const bgValue = ref('')
const uploadedImages = ref<string[]>([])
const currentAccent = ref('#6c5ce7')

const gradients = [
  { value: 'linear-gradient(135deg, #0f0f1a, #1a1a2e)' },
  { value: 'linear-gradient(135deg, #1a1a2e, #6c5ce7)' },
  { value: 'linear-gradient(135deg, #0f0f1a, #00b894)' },
  { value: 'linear-gradient(135deg, #2d3436, #636e72)' },
  { value: 'linear-gradient(135deg, #dfe6e9, #b2bec3)' },
  { value: 'linear-gradient(135deg, #fdcb6e, #e17055)' },
]

const accentColors = ['#6c5ce7', '#00b894', '#0984e3', '#e17055', '#fdcb6e', '#fd79a8', '#a29bfe', '#636e72']

function applyBg() {
  const root = document.documentElement
  if (activeBgType.value === 'color') {
    root.style.setProperty('--bg-primary', bgColor.value)
    root.style.backgroundImage = 'none'
  } else if (activeBgType.value === 'gradient') {
    root.style.backgroundImage = bgValue.value
  } else if (activeBgType.value === 'image') {
    root.style.backgroundImage = `url(${bgValue.value})`
    root.style.backgroundSize = 'cover'
    root.style.backgroundPosition = 'center'
  }
  // Save preference
  localStorage.setItem('wp_bg_type', activeBgType.value)
  localStorage.setItem('wp_bg_value', bgValue.value || bgColor.value)
}

async function handleImageUpload(file: any) {
  const url = URL.createObjectURL(file.raw)
  uploadedImages.value.push(url)
  bgValue.value = url
  applyBg()

  // Upload to server
  const fd = new FormData()
  fd.append('file', file.raw)
  fd.append('bg_type', 'image')
  try {
    const { data } = await createBackground(fd)
    await setActiveBackground(data.id)
    ElMessage.success('壁纸已上传')
  } catch { /* local only */ }
}

function setAccent(color: string) {
  currentAccent.value = color
  document.documentElement.style.setProperty('--accent', color)
  document.documentElement.style.setProperty('--accent-gradient', `linear-gradient(135deg, ${color}, ${color}88)`)
  localStorage.setItem('wp_accent', color)
}

onMounted(async () => {
  const savedBgType = localStorage.getItem('wp_bg_type')
  const savedBgValue = localStorage.getItem('wp_bg_value')
  const savedAccent = localStorage.getItem('wp_accent')
  if (savedBgType) activeBgType.value = savedBgType
  if (savedBgValue) { bgValue.value = savedBgValue; if (activeBgType.value === 'color') bgColor.value = savedBgValue }
  if (savedAccent) setAccent(savedAccent)
  applyBg()

  try {
    const { data } = await getActiveBackground()
    if (data.bg_type) { activeBgType.value = data.bg_type; bgValue.value = data.bg_value; applyBg() }
  } catch { /* */ }
})
</script>

<style scoped>
.personalization { max-width: 900px; margin: 0 auto; }
.page-header { margin-bottom: 24px; }
.page-header h2 { display: flex; align-items: center; gap: 8px; font-size: 22px; font-weight: 800; }
.settings-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.setting-card { padding: 20px; }
.setting-card h3 { font-size: 16px; font-weight: 700; margin-bottom: 14px; }
.gradient-presets { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.gradient-block { height: 60px; border-radius: 10px; cursor: pointer; border: 2px solid transparent; transition: all var(--transition); }
.gradient-block.active, .gradient-block:hover { border-color: var(--accent); transform: scale(1.05); }
.upload-area { padding: 24px; text-align: center; }
.upload-area p { font-size: 13px; color: var(--text-secondary); margin-top: 8px; }
.image-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.img-thumb { height: 60px; border-radius: 10px; background-size: cover; background-position: center; cursor: pointer; border: 2px solid transparent; }
.img-thumb.active { border-color: var(--accent); }
.accent-colors { display: flex; gap: 10px; flex-wrap: wrap; }
.accent-dot { width: 36px; height: 36px; border-radius: 50%; cursor: pointer; border: 2px solid transparent; transition: transform 0.2s; }
.accent-dot.active, .accent-dot:hover { border-color: white; transform: scale(1.15); box-shadow: 0 0 12px rgba(0,0,0,0.3); }
@media (max-width: 768px) { .settings-grid { grid-template-columns: 1fr; } }
</style>
