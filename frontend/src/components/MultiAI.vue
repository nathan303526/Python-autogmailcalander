<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import axios from 'axios'
import { API_BASE } from '../config'

const openaiKey = ref('')
const geminiKey = ref('')

// 模型選擇
const openaiModel = ref('gpt-3.5-turbo')
const geminiModel = ref('gemini-2.5-flash')

const openaiModels = ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo', 'gpt-4o']
const geminiModels = [
  'gemini-2.5-flash',
  'gemini-2.5-pro',
  'gemini-2.0-flash',
  'gemini-flash-latest',
  'gemini-pro-latest'
]

// 獨立輸入框
const openaiInput = ref('')
const geminiInput = ref('')
// 全局輸入框
const globalInput = ref('')

const openaiMessages = ref([])
const geminiMessages = ref([])

const isLoadingOpenAI = ref(false)
const isLoadingGemini = ref(false)

const openaiContainer = ref(null)
const geminiContainer = ref(null)

// 初始化讀取 Token
onMounted(() => {
  const storedOpenAI = sessionStorage.getItem('openai_key')
  const storedGemini = sessionStorage.getItem('gemini_key')
  if (storedOpenAI) openaiKey.value = storedOpenAI
  if (storedGemini) geminiKey.value = storedGemini
})

// 監聽並儲存 Token
watch(openaiKey, (newVal) => sessionStorage.setItem('openai_key', newVal))
watch(geminiKey, (newVal) => sessionStorage.setItem('gemini_key', newVal))

const clearKeys = () => {
  openaiKey.value = ''
  geminiKey.value = ''
  sessionStorage.removeItem('openai_key')
  sessionStorage.removeItem('gemini_key')
}

const scrollToBottom = async (containerRef) => {
  await nextTick()
  if (containerRef.value) {
    containerRef.value.scrollTop = containerRef.value.scrollHeight
  }
}

// 真實 API 請求
const callApi = async (provider, prompt, key, model) => {
  if (!key) return `請輸入 ${provider} API Key 以取得回應`
  
  try {
    const endpoint = provider === 'OpenAI' ? '/chat/openai' : '/chat/gemini'
    const res = await axios.post(`${API_BASE}${endpoint}`, {
      prompt: prompt,
      api_key: key,
      model: model
    }, { timeout: 30000 }) // 設定 30 秒超時
    
    if (res.data.error) {
      return `[API 錯誤]: ${res.data.error}`
    }
    return res.data.response
  } catch (error) {
    console.error(error)
    if (error.code === 'ECONNABORTED') {
      return `[連線逾時]: 請求超過 30 秒未回應，請稍後再試。`
    }
    return `[連線錯誤]: ${error.message}`
  }
}

// 發送給 OpenAI
const sendOpenAI = async () => {
  const text = openaiInput.value.trim()
  if (!text) return
  
  openaiMessages.value.push({ role: 'user', content: text })
  openaiInput.value = ''
  isLoadingOpenAI.value = true
  scrollToBottom(openaiContainer)

  const response = await callApi('OpenAI', text, openaiKey.value, openaiModel.value)
  openaiMessages.value.push({ role: 'assistant', content: response })
  isLoadingOpenAI.value = false
  scrollToBottom(openaiContainer)
}

// 發送給 Gemini
const sendGemini = async () => {
  const text = geminiInput.value.trim()
  if (!text) return

  geminiMessages.value.push({ role: 'user', content: text })
  geminiInput.value = ''
  isLoadingGemini.value = true
  scrollToBottom(geminiContainer)

  const response = await callApi('Gemini', text, geminiKey.value, geminiModel.value)
  geminiMessages.value.push({ role: 'assistant', content: response })
  isLoadingGemini.value = false
  scrollToBottom(geminiContainer)
}

// 同時發送
const sendGlobal = async () => {
  const text = globalInput.value.trim()
  if (!text) return

  // 同步更新兩個對話框的輸入狀態 (模擬使用者分別輸入)
  openaiMessages.value.push({ role: 'user', content: text })
  geminiMessages.value.push({ role: 'user', content: text })
  
  globalInput.value = ''
  
  isLoadingOpenAI.value = true
  isLoadingGemini.value = true
  
  scrollToBottom(openaiContainer)
  scrollToBottom(geminiContainer)

  // 平行處理請求
  const [resOpenAI, resGemini] = await Promise.all([
    callApi('OpenAI', text, openaiKey.value, openaiModel.value),
    callApi('Gemini', text, geminiKey.value, geminiModel.value)
  ])

  openaiMessages.value.push({ role: 'assistant', content: resOpenAI })
  geminiMessages.value.push({ role: 'assistant', content: resGemini })

  isLoadingOpenAI.value = false
  isLoadingGemini.value = false
  
  scrollToBottom(openaiContainer)
  scrollToBottom(geminiContainer)
}
</script>

<template>
  <div class="bg-gray-800 p-4 rounded-2xl shadow-lg border border-gray-700 h-[85vh] flex flex-col max-w-6xl mx-auto w-full">
    <div class="flex justify-between items-center mb-3">
      <h2 class="text-xl font-bold text-white flex items-center gap-2">
        <span>🤖</span> 多模組 AI 助手
      </h2>
      <div class="flex items-center gap-3">
        <div class="text-xs text-gray-500 hidden md:block">
          Token 存於 SessionStorage (關閉即清除)
        </div>
        <button 
          @click="clearKeys"
          class="text-xs bg-red-900/30 hover:bg-red-800/50 text-red-300 px-3 py-1.5 rounded border border-red-800/50 transition"
        >
          清除金鑰
        </button>
      </div>
    </div>

    <!-- Token 與模型設定區 -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
      <!-- OpenAI 設定 -->
      <div class="flex gap-2">
        <input 
          v-model="openaiKey" 
          type="password" 
          placeholder="OpenAI API Key (sk-...)" 
          class="flex-1 bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-green-500 placeholder-gray-600"
        >
        <select 
          v-model="openaiModel"
          class="bg-gray-900 border border-gray-600 rounded-lg px-2 py-2 text-sm text-white focus:outline-none focus:border-green-500"
        >
          <option v-for="model in openaiModels" :key="model" :value="model">{{ model }}</option>
        </select>
      </div>

      <!-- Gemini 設定 -->
      <div class="flex gap-2">
        <input 
          v-model="geminiKey" 
          type="password" 
          placeholder="Gemini API Key (AIza...)" 
          class="flex-1 bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500 placeholder-gray-600"
        >
        <select 
          v-model="geminiModel"
          class="bg-gray-900 border border-gray-600 rounded-lg px-2 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
        >
          <option v-for="model in geminiModels" :key="model" :value="model">{{ model }}</option>
        </select>
      </div>
    </div>

    <!-- 雙 AI 對話區 (Flex 並排) -->
    <div class="flex-1 flex gap-3 min-h-0 mb-3">
      
      <!-- OpenAI 面板 -->
      <div class="flex-1 flex flex-col bg-gray-900/30 rounded-xl border border-green-900/30 overflow-hidden relative">
        <!-- 遮罩層 (無 Key 時顯示) -->
        <div v-if="!openaiKey" class="absolute inset-0 bg-gray-900/80 backdrop-blur-sm z-10 flex items-center justify-center text-gray-400 text-sm">
          請輸入 OpenAI API Key 以解鎖
        </div>

        <div class="p-3 bg-green-900/20 border-b border-green-900/30 font-bold text-green-400 flex justify-between items-center">
          <span>ChatGPT</span>
          <span v-if="isLoadingOpenAI" class="text-xs animate-pulse">思考中...</span>
        </div>
        
        <!-- 訊息列表 -->
        <div ref="openaiContainer" class="flex-1 overflow-y-auto p-4 space-y-4" :class="{ 'blur-sm select-none': !openaiKey }">
          <div v-if="openaiMessages.length === 0" class="text-center text-gray-600 mt-10 text-sm">
            尚無對話紀錄
          </div>
          <div v-for="(msg, idx) in openaiMessages" :key="idx" :class="msg.role === 'user' ? 'text-right' : 'text-left'">
            <div 
              class="inline-block px-3 py-2 rounded-lg text-sm max-w-[90%]"
              :class="msg.role === 'user' ? 'bg-green-600 text-white' : 'bg-gray-700 text-gray-200'"
            >
              {{ msg.content }}
            </div>
          </div>
        </div>

        <!-- 個別輸入框 -->
        <div class="p-2 border-t border-gray-700 bg-gray-800/50">
          <div class="flex gap-2">
            <input 
              v-model="openaiInput" 
              @keyup.enter="sendOpenAI"
              type="text" 
              :disabled="!openaiKey"
              placeholder="發送給 ChatGPT..." 
              class="flex-1 bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
            <button @click="sendOpenAI" :disabled="!openaiKey" class="text-green-500 hover:text-green-400 px-2 disabled:opacity-50 disabled:cursor-not-allowed">
              ➤
            </button>
          </div>
        </div>
      </div>

      <!-- Gemini 面板 -->
      <div class="flex-1 flex flex-col bg-gray-900/30 rounded-xl border border-blue-900/30 overflow-hidden relative">
        <!-- 遮罩層 (無 Key 時顯示) -->
        <div v-if="!geminiKey" class="absolute inset-0 bg-gray-900/80 backdrop-blur-sm z-10 flex items-center justify-center text-gray-400 text-sm">
          請輸入 Gemini API Key 以解鎖
        </div>

        <div class="p-3 bg-blue-900/20 border-b border-blue-900/30 font-bold text-blue-400 flex justify-between items-center">
          <span>Gemini</span>
          <span v-if="isLoadingGemini" class="text-xs animate-pulse">思考中...</span>
        </div>

        <!-- 訊息列表 -->
        <div ref="geminiContainer" class="flex-1 overflow-y-auto p-4 space-y-4" :class="{ 'blur-sm select-none': !geminiKey }">
          <div v-if="geminiMessages.length === 0" class="text-center text-gray-600 mt-10 text-sm">
            尚無對話紀錄
          </div>
          <div v-for="(msg, idx) in geminiMessages" :key="idx" :class="msg.role === 'user' ? 'text-right' : 'text-left'">
            <div 
              class="inline-block px-3 py-2 rounded-lg text-sm max-w-[90%]"
              :class="msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-200'"
            >
              {{ msg.content }}
            </div>
          </div>
        </div>

        <!-- 個別輸入框 -->
        <div class="p-2 border-t border-gray-700 bg-gray-800/50">
          <div class="flex gap-2">
            <input 
              v-model="geminiInput" 
              @keyup.enter="sendGemini"
              type="text" 
              :disabled="!geminiKey"
              placeholder="發送給 Gemini..." 
              class="flex-1 bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
            <button @click="sendGemini" :disabled="!geminiKey" class="text-blue-500 hover:text-blue-400 px-2 disabled:opacity-50 disabled:cursor-not-allowed">
              ➤
            </button>
          </div>
        </div>
      </div>

    </div>

    <!-- 全局輸入區 -->
    <div class="relative">
      <input 
        v-model="globalInput" 
        @keyup.enter="sendGlobal"
        type="text" 
        placeholder="同時發送給兩個 AI..." 
        class="w-full bg-gray-700 border border-gray-600 rounded-xl px-4 py-4 pr-24 text-white focus:outline-none focus:border-purple-500 shadow-lg"
      >
      <button 
        @click="sendGlobal" 
        :disabled="isLoadingOpenAI || isLoadingGemini"
        class="absolute right-2 top-2 bottom-2 bg-purple-600 hover:bg-purple-500 text-white px-6 rounded-lg font-bold transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
      >
        發送全部
      </button>
    </div>
  </div>
</template>