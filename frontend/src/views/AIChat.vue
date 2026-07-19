<template>
  <div class="ai-chat-page">
    <div class="chat-layout">
      <div class="chat-sidebar glass">
        <div class="sidebar-header"><h3>AI 对话</h3></div>
        <div class="web-ai-section">
          <div class="section-label">🌐 网页 AI</div>
          <div class="section-hint">点击在新标签页打开（无需 Token）</div>
          <div class="web-ai-list">
            <div v-for="p in webProviders" :key="p.id" class="web-ai-chip glass-hover" @click="openInTab(p)">
              <span>{{ p.name }}</span><el-icon size="12"><TopRight /></el-icon>
            </div>
          </div>
        </div>
        <el-divider />
        <div class="web-ai-section">
          <div class="section-label">⚡ 站内对话</div>
          <div class="section-hint">配置 API Key 后直接在本页聊天</div>
          <div class="web-ai-list">
            <div v-for="p in apiProviders" :key="p.id" :class="['web-ai-chip','glass-hover',{active:selectedProvider===p.id}]" @click="selectAPIProvider(p)">
              <span>{{ p.name }}</span>
              <span v-if="!p.api_key" class="no-key-tag">未配置</span>
              <span v-else class="has-key-tag">✓</span>
            </div>
          </div>
          <div v-if="!apiProviders.length" class="empty-hint">去「AI 工具」页面把任意 AI 的 API 类型改为非"仅网页"即可</div>
        </div>
      </div>

      <div class="chat-main">
        <template v-if="activeMode==='api'">
          <div class="chat-header glass">
            <span class="chat-model-info"><b>{{ selectedProviderObj?.name||'选择 AI' }}</b></span>
            <div class="chat-header-right">
              <el-button v-if="!selectedProviderObj?.api_key" size="small" type="primary" @click="goConfigKey">配置 API Key</el-button>
              <el-input v-else v-model="modelName" placeholder="模型名 (可选)" size="small" style="width:180px" />
            </div>
          </div>
          <div class="messages-area" ref="msgContainer">
            <div v-for="(msg,i) in messages" :key="i" :class="['message',msg.role]">
              <div class="msg-avatar">{{ msg.role==='user'?'👤':'🤖' }}</div>
              <div class="msg-content" v-html="renderMarkdown(msg.content)"></div>
              <el-button v-if="msg.role==='assistant'" text size="small" class="msg-copy" @click="copyText(msg.content)"><el-icon size="14"><CopyDocument /></el-icon></el-button>
            </div>
            <div v-if="streaming" class="message assistant"><div class="msg-avatar">🤖</div><div class="msg-content typing-indicator"><span></span><span></span><span></span></div></div>
            <div v-if="!messages.length&&!streaming&&selectedProviderObj?.api_key" class="no-messages"><div class="no-msg-icon">💬</div><p>输入问题开始对话</p></div>
            <div v-if="!messages.length&&!streaming&&!selectedProviderObj?.api_key&&selectedProviderObj" class="no-messages"><div class="no-msg-icon">🔑</div><p>此 AI 尚未配置 API Key</p><el-button type="primary" size="small" @click="goConfigKey">去配置</el-button></div>
          </div>
          <div class="chat-input glass">
            <el-input v-model="userInput" type="textarea" :rows="3" placeholder="输入消息... Enter 发送" @keydown.enter.exact.prevent="sendMessage" resize="none" :disabled="!selectedProviderObj?.api_key" />
            <div class="input-actions">
              <el-button size="small" @click="insertPrompt"><el-icon><Document /></el-icon> Prompt</el-button>
              <el-button size="small" type="primary" @click="sendMessage" :loading="streaming" :disabled="!userInput.trim()">发送</el-button>
            </div>
          </div>
        </template>

        <template v-else>
          <div class="welcome-chat glass">
            <h2>🤖 AI 聚合中心</h2>
            <p>选择左侧「站内对话」AI 即可在本页直接聊天，无需跳转</p>
            <div class="welcome-cards">
              <div class="welcome-card glass glass-hover" @click="router.push('/ai')"><el-icon size="28"><Setting /></el-icon><span>管理 AI 工具</span></div>
              <div class="welcome-card glass glass-hover" @click="router.push('/ai-compare')"><el-icon size="28"><Connection /></el-icon><span>多模型对比</span></div>
              <div class="welcome-card glass glass-hover" @click="router.push('/prompts')"><el-icon size="28"><Document /></el-icon><span>Prompt 管理</span></div>
            </div>
          </div>
        </template>
      </div>
    </div>

    <el-dialog v-model="showPromptPicker" title="选择 Prompt" width="520px">
      <el-input v-model="promptSearch" placeholder="搜索 Prompt..." class="mb-3" clearable />
      <div class="prompt-list-dialog">
        <div v-for="p in filteredPrompts" :key="p.id" class="prompt-option" @click="usePrompt(p)"><b>{{ p.title }}</b><span class="text-xs text-muted">{{ p.category }}</span></div>
        <el-empty v-if="!filteredPrompts.length" description="暂无匹配 Prompt" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { aiChat, getChatHistory, createChatHistory, updateChatHistory, deleteChatHistory, getAIProviders, getPrompts } from '../api'
import MarkdownIt from 'markdown-it'
import { ElMessage } from 'element-plus'

const router = useRouter()
const md = new MarkdownIt({ breaks: true, linkify: true })
const allProviders = ref<any[]>([])
const selectedProvider = ref<number | null>(null)
const activeMode = ref<'api' | ''>('')
const modelName = ref('')
const messages = ref<{ role: string; content: string }[]>([])
const userInput = ref('')
const streaming = ref(false)
const histories = ref<any[]>([])
const currentChatId = ref<number | null>(null)
const msgContainer = ref<HTMLElement | null>(null)
const showPromptPicker = ref(false)
const promptSearch = ref('')
const allPrompts = ref<any[]>([])

const webProviders = computed(() => allProviders.value.filter((p: any) => p.is_enabled && p.api_type === 'web'))
const apiProviders = computed(() => allProviders.value.filter((p: any) => p.is_enabled && p.api_type !== 'web'))
const selectedProviderObj = computed(() => allProviders.value.find((p: any) => p.id === selectedProvider.value))
const filteredPrompts = computed(() => { const q = promptSearch.value.toLowerCase(); return q ? allPrompts.value.filter((p: any) => p.title.toLowerCase().includes(q) || p.content.toLowerCase().includes(q)) : allPrompts.value })

function renderMarkdown(text: string) { return md.render(text || '') }
function copyText(text: string) { navigator.clipboard.writeText(text); ElMessage.success('已复制') }
function openInTab(p: any) { window.open(p.url, '_blank') }
function goConfigKey() { router.push('/ai') }
function selectAPIProvider(p: any) { selectedProvider.value = p.id; activeMode.value = 'api'; messages.value = []; modelName.value = p.api_type === 'deepseek' ? 'deepseek-chat' : '' }

async function sendMessage() {
  if (!userInput.value.trim() || !selectedProvider.value) return
  if (!selectedProviderObj.value?.api_key) { ElMessage.warning('请先去 AI 工具页面为此 AI 配置 API Key'); return }
  messages.value.push({ role: 'user', content: userInput.value })
  const input = userInput.value; userInput.value = ''; streaming.value = true
  await scrollToBottom()
  try {
    const { data } = await aiChat({ provider_id: selectedProvider.value, model: modelName.value, messages: messages.value.map(m => ({ role: m.role, content: m.content })), stream: false })
    messages.value.push({ role: 'assistant', content: data?.choices?.[0]?.message?.content || '(无回复)' })
    await saveCurrentChat()
  } catch (e: any) { messages.value.push({ role: 'assistant', content: `❌ ${e?.response?.data?.detail || e.message}` }) }
  streaming.value = false; await scrollToBottom()
}

async function scrollToBottom() { await nextTick(); if (msgContainer.value) msgContainer.value.scrollTop = msgContainer.value.scrollHeight }
function newChat() { messages.value = []; currentChatId.value = null; userInput.value = '' }
async function saveCurrentChat() {
  const title = messages.value[0]?.content?.slice(0, 50) || '新对话'
  if (currentChatId.value) { await updateChatHistory(currentChatId.value, { title, messages: JSON.stringify(messages.value) }) }
  else if (messages.value.length > 0) { const { data } = await createChatHistory({ title, provider_id: selectedProvider.value, model: modelName.value }); currentChatId.value = data.id; await updateChatHistory(data.id, { messages: JSON.stringify(messages.value) }) }
  await loadHistories()
}
async function loadChat(chat: any) { currentChatId.value = chat.id; selectedProvider.value = chat.provider_id; activeMode.value = 'api'; try { messages.value = JSON.parse(chat.messages || '[]') } catch { messages.value = [] } }
async function deleteChat(id: number) { await deleteChatHistory(id); if (currentChatId.value === id) { messages.value = []; currentChatId.value = null }; await loadHistories() }
async function loadHistories() { try { const { data } = await getChatHistory(); histories.value = data } catch { histories.value = [] } }
async function insertPrompt() { showPromptPicker.value = true; try { const { data } = await getPrompts(); allPrompts.value = data } catch { allPrompts.value = [] } }
function usePrompt(p: any) { userInput.value = p.content; showPromptPicker.value = false }

onMounted(async () => { try { const { data } = await getAIProviders(); allProviders.value = data } catch { /* */ }; await loadHistories() })
</script>

<style scoped>
.ai-chat-page { max-width: 1400px; margin: 0 auto; height: calc(100vh - 170px); }
.chat-layout { display: flex; gap: 12px; height: 100%; }
.chat-sidebar { width: 240px; flex-shrink: 0; display: flex; flex-direction: column; overflow-y: auto; padding-bottom: 8px; }
.sidebar-header { padding: 14px 14px 4px; }
.sidebar-header h3 { font-size: 15px; font-weight: 700; }
.web-ai-section { padding: 6px 10px; }
.section-label { font-size: 12px; font-weight: 700; padding: 4px 4px 2px; }
.section-hint { font-size: 10px; color: var(--text-muted); padding: 0 4px 4px; }
.web-ai-list { display: flex; flex-direction: column; gap: 1px; }
.web-ai-chip { display: flex; align-items: center; justify-content: space-between; padding: 7px 10px; border-radius: 7px; cursor: pointer; font-size: 13px; transition: all 0.12s; }
.web-ai-chip:hover { background: var(--bg-primary); }
.web-ai-chip.active { background: var(--accent); color: white; }
.no-key-tag { font-size: 10px; color: #e17055; }
.has-key-tag { font-size: 11px; color: #00b894; font-weight: 700; }
.empty-hint { font-size: 11px; color: var(--text-muted); padding: 4px 10px; line-height: 1.4; }
.chat-main { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.chat-header { display: flex; align-items: center; justify-content: space-between; padding: 10px 16px; margin-bottom: 6px; }
.chat-model-info { font-size: 14px; }
.chat-header-right { display: flex; gap: 8px; align-items: center; }
.messages-area { flex: 1; overflow-y: auto; padding: 4px 0; }
.message { display: flex; gap: 10px; padding: 10px 16px; position: relative; }
.message.user { background: var(--bg-primary); }
.msg-avatar { width: 30px; height: 30px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 16px; flex-shrink: 0; }
.msg-content { flex: 1; font-size: 14px; line-height: 1.75; overflow-wrap: break-word; min-width: 0; }
.msg-content :deep(p) { margin: 4px 0; }
.msg-content :deep(pre) { background: var(--bg-primary); padding: 10px 14px; border-radius: 8px; overflow-x: auto; font-size: 13px; margin: 8px 0; }
.msg-copy { opacity: 0; position: absolute; right: 8px; top: 8px; transition: opacity 0.15s; }
.message:hover .msg-copy { opacity: 1; }
.no-messages { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; gap: 10px; color: var(--text-muted); }
.no-msg-icon { font-size: 48px; }
.chat-input { padding: 10px 16px; margin-top: 6px; }
.input-actions { display: flex; justify-content: flex-end; gap: 6px; margin-top: 8px; }
.typing-indicator span { display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: var(--text-muted); margin: 0 2px; animation: typingBounce 1.4s infinite; }
.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
@keyframes typingBounce { 0%,60%,100% { transform: translateY(0); } 30% { transform: translateY(-6px); } }
.welcome-chat { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 6px; margin: 8px; padding: 32px; }
.welcome-chat h2 { font-size: 26px; }
.welcome-chat>p { color: var(--text-secondary); font-size: 14px; }
.welcome-cards { display: flex; gap: 12px; margin-top: 12px; }
.welcome-card { display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 18px 22px; cursor: pointer; text-align: center; font-size: 13px; font-weight: 600; }
.prompt-list-dialog { max-height: 320px; overflow-y: auto; }
.prompt-option { padding: 12px; border-radius: 8px; cursor: pointer; border: 1px solid var(--border-color); margin-bottom: 6px; display: flex; justify-content: space-between; }
.prompt-option:hover { background: var(--bg-primary); border-color: var(--accent); }
@media (max-width: 768px) { .chat-sidebar { display: none; } }
</style>
