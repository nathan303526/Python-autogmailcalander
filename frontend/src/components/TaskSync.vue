<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const tasks = ref([])
const isLoading = ref(false)
const API_BASE = 'http://localhost:8000/api'

// Google 整合相關狀態
const isConfigured = ref(false)
const uploading = ref(false)
const uploadMessage = ref('')
const uploadStatus = ref('')
const fileInput = ref(null)

// 檢查後端是否已設定憑證
const checkGoogleStatus = async () => {
  try {
    // 這裡假設有一個 API 可以檢查狀態，暫時先模擬
    // const res = await axios.get(`${API_BASE}/google/status`)
    // isConfigured.value = res.data.configured
    isConfigured.value = false // 預設先顯示上傳介面供測試
  } catch (error) {
    console.error('Status check failed', error)
  }
}

const handleFileUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  const formData = new FormData()
  formData.append('file', file)

  uploading.value = true
  uploadMessage.value = ''
  
  try {
    await axios.post(`${API_BASE}/google/upload-credentials`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    uploadStatus.value = 'success'
    uploadMessage.value = '憑證上傳成功！系統將自動進行下一步設定。'
    isConfigured.value = true
    // 上傳成功後，可能需要觸發 OAuth 流程，這裡先保留
  } catch (error) {
    uploadStatus.value = 'error'
    uploadMessage.value = '上傳失敗: ' + (error.response?.data?.detail || error.message)
  } finally {
    uploading.value = false
  }
}

onMounted(() => {
  checkGoogleStatus()
})

const syncTasks = async () => {
  isLoading.value = true
  tasks.value = [] // 清空舊資料
  try {
    const res = await axios.get(`${API_BASE}/sync-tasks`)
    tasks.value = res.data
  } catch (error) {
    console.error('Error syncing tasks:', error)
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="bg-gray-800 flex-1 rounded-2xl p-8 shadow-lg border border-gray-700 flex flex-col">
    <div class="flex justify-between items-center mb-8">
      <div>
        <h1 class="text-3xl font-bold text-white mb-2">智慧待辦助理</h1>
        <p class="text-gray-400">AI 自動分析您的 Gmail 與 Calendar，生成最佳行動建議。</p>
      </div>
      <button 
        @click="syncTasks"
        :disabled="isLoading || !isConfigured"
        class="bg-blue-600 hover:bg-blue-500 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-bold py-3 px-8 rounded-xl transition duration-300 flex items-center gap-2 shadow-lg"
      >
        <span v-if="isLoading" class="animate-spin">⏳</span>
        <span v-else>⚡</span>
        {{ isLoading ? '分析中...' : '開始同步' }}
      </button>
    </div>

    <!-- Google 憑證設定區 (未設定時顯示) -->
    <div v-if="!isConfigured" class="mb-8 p-6 bg-gray-700/30 rounded-xl border border-dashed border-gray-500">
      <div class="flex flex-col items-center text-center">
        <div class="text-4xl mb-3">🔐</div>
        <h2 class="text-xl font-bold text-white mb-2">需要 Google 授權</h2>
        <p class="text-gray-300 mb-6 max-w-lg">
          為了讓 AI 分析您的郵件與行事曆，請上傳您的 OAuth 2.0 憑證 (client_secret.json)。
          <br><span class="text-xs text-gray-500">請至 Google Cloud Console 下載憑證</span>
        </p>
        
        <div class="w-full max-w-md">
          <label class="block w-full cursor-pointer">
            <input 
              type="file" 
              ref="fileInput"
              accept=".json"
              @change="handleFileUpload"
              class="hidden"
            />
            <div class="flex items-center justify-center gap-3 px-6 py-4 bg-gray-600 hover:bg-gray-500 rounded-lg transition border border-gray-500">
              <span class="text-2xl">📂</span>
              <span class="text-white font-medium">點擊上傳 client_secret.json</span>
            </div>
          </label>
          
          <div v-if="uploading" class="mt-3 text-blue-400 animate-pulse">
            正在上傳並驗證憑證...
          </div>
          
          <div v-if="uploadMessage" 
            class="mt-3 p-3 rounded-lg text-sm font-medium"
            :class="uploadStatus === 'success' ? 'bg-green-900/50 text-green-300' : 'bg-red-900/50 text-red-300'"
          >
            {{ uploadMessage }}
          </div>
        </div>
      </div>
    </div>

    <!-- 列表顯示區 -->
    <div class="flex-1 overflow-y-auto pr-2">
      
      <!-- Loading State -->
      <div v-if="isLoading" class="flex flex-col items-center justify-center h-64 text-gray-500 space-y-4">
        <div class="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        <p>正在連線至 AI 核心進行分析...</p>
      </div>

      <!-- Empty State -->
      <div v-else-if="tasks.length === 0" class="flex flex-col items-center justify-center h-64 text-gray-600">
        <div class="text-6xl mb-4">📭</div>
        <p>目前沒有待辦事項，請點擊上方按鈕進行同步。</p>
      </div>

      <!-- Task List -->
      <div v-else class="space-y-4">
        <div v-for="(task, index) in tasks" :key="index" 
          class="bg-gray-700/50 p-5 rounded-xl flex items-center justify-between hover:bg-gray-700 transition border border-gray-600"
        >
          <div class="flex items-center gap-4">
            <div class="w-10 h-10 rounded-full flex items-center justify-center"
              :class="{
                'bg-green-900/50 text-green-400': task.status === 'success',
                'bg-yellow-900/50 text-yellow-400': task.status === 'pending'
              }"
            >
              {{ task.status === 'success' ? '✓' : '!' }}
            </div>
            <div>
              <h3 class="font-bold text-lg text-white">{{ task.title }}</h3>
              <p class="text-sm text-gray-400">建議行動: {{ task.action }}</p>
            </div>
          </div>
          <span class="px-3 py-1 rounded-full text-xs font-medium uppercase tracking-wider"
            :class="{
              'bg-green-900 text-green-300': task.status === 'success',
              'bg-yellow-900 text-yellow-300': task.status === 'pending'
            }"
          >
            {{ task.status }}
          </span>
        </div>
      </div>

    </div>
  </div>
</template>
