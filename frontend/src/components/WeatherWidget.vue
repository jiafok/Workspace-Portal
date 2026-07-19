<template>
  <div class="weather-widget glass glass-hover" v-if="hasWeather" @click="openWeather">
    <span class="weather-icon">{{ weatherIcon }}</span>
    <div class="weather-info">
      <span class="weather-temp">{{ temp }}°</span>
      <span class="weather-city">{{ city }}</span>
    </div>
  </div>
  <div v-else class="weather-widget glass dimmed" @click="openConfig">
    <el-icon><Setting /></el-icon>
    <span class="text-xs text-muted">配置天气</span>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../api'

const hasWeather = ref(false)
const temp = ref('--')
const city = ref('--')
const weatherIcon = ref('☀️')

async function fetchWeather() {
  try {
    // Try to read weather plugin config
    const { data } = await api.get('/plugins')
    const weatherPlugin = data.find((p: any) => p.plugin_id === 'weather-widget' && p.is_enabled)
    if (weatherPlugin) {
      const config = JSON.parse(weatherPlugin.config_data || '{}')
      if (config.api_key && config.city) {
        const resp = await fetch(
          `https://api.openweathermap.org/data/2.5/weather?q=${config.city}&appid=${config.api_key}&units=${config.units || 'metric'}&lang=zh_cn`
        )
        if (resp.ok) {
          const w = await resp.json()
          temp.value = Math.round(w.main.temp)
          city.value = w.name
          const code = w.weather[0].id
          if (code >= 200 && code < 300) weatherIcon.value = '⛈️'
          else if (code >= 300 && code < 600) weatherIcon.value = '🌧️'
          else if (code >= 600 && code < 700) weatherIcon.value = '❄️'
          else if (code >= 700 && code < 800) weatherIcon.value = '🌫️'
          else if (code === 800) weatherIcon.value = '☀️'
          else weatherIcon.value = '⛅'
          hasWeather.value = true
          return
        }
      }
    }
  } catch { /* */ }
  hasWeather.value = false
}

function openWeather() {}
function openConfig() {}

onMounted(fetchWeather)
</script>

<style scoped>
.weather-widget { display: flex; align-items: center; gap: 8px; padding: 6px 12px; cursor: pointer; }
.weather-icon { font-size: 20px; }
.weather-info { display: flex; flex-direction: column; }
.weather-temp { font-size: 15px; font-weight: 700; }
.weather-city { font-size: 10px; color: var(--text-muted); }
.dimmed { opacity: 0.5; font-size: 12px; gap: 4px; }
</style>
