<template>
  <div class="bookmark-import">
    <el-upload
      drag
      :auto-upload="false"
      accept=".html,.htm"
      :on-change="handleFile"
      :show-file-list="false"
    >
      <div class="upload-area">
        <el-icon size="40" color="var(--accent)"><UploadFilled /></el-icon>
        <p>拖拽或点击导入收藏夹</p>
        <p class="upload-hint">支持 Chrome / Edge / Firefox 导出的 HTML 收藏夹文件</p>
      </div>
    </el-upload>
    <div v-if="importResult" class="import-result">
      <el-alert
        :title="`成功导入 ${importResult.imported_categories} 个分类，${importResult.imported_websites} 个网站`"
        type="success"
        closable
        @close="importResult = null"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { importBookmarks } from '../api'

const emit = defineEmits(['done'])
const importResult = ref<any>(null)

async function handleFile(file: any) {
  const text = await file.raw.text()
  try {
    const { data } = await importBookmarks(text)
    importResult.value = data
    emit('done')
  } catch (e: any) {
    importResult.value = { error: e.message || '导入失败' }
  }
}
</script>

<style scoped>
.bookmark-import {
  padding: 8px 0;
}
.upload-area {
  padding: 32px;
  text-align: center;
}
.upload-area p {
  margin-top: 8px;
  font-size: 14px;
  color: var(--text-secondary);
}
.upload-hint {
  font-size: 12px !important;
  color: var(--text-muted) !important;
}
.import-result {
  margin-top: 12px;
}
</style>
