<script setup>
import { ref } from 'vue'
import axios from 'axios'

const props = defineProps({
  show: Boolean,
  token: String
})

const emit = defineEmits(['close', 'enabled'])

const step = ref(1) // 1: Show QR, 2: Verify
const qrCodeUrl = ref('')
const code = ref('')
const loading = ref(false)
const error = ref('')

const api = axios.create({
  baseURL: 'http://localhost:8000'
})

const startSetup = async () => {
  loading.value = true
  error.value = ''
  try {
    const res = await api.get('/api/auth/2fa/setup', {
      headers: { Authorization: `Bearer ${props.token}` },
      responseType: 'blob'
    })
    qrCodeUrl.value = URL.createObjectURL(res.data)
    step.value = 1
  } catch (e) {
    error.value = '無法取得 QR Code'
  } finally {
    loading.value = false
  }
}

const verifySetup = async () => {
  loading.value = true
  error.value = ''
  try {
    // 這裡假設我們需要傳入 username，但 API 需要從 token 解析 user
    // 不過 verify_2fa API 需要 username in body
    // 我們需要先知道 username。通常從 token 解析，或者從父組件傳入。
    // 為了簡單，我們修改一下 verify_2fa API 或者先獲取 user info
    
    // 先獲取 user info
    const userRes = await api.get('/api/users/me', {
      headers: { Authorization: `Bearer ${props.token}` }
    })
    const username = userRes.data.username

    await api.post('/api/auth/2fa/verify', {
      username: username,
      code: code.value
    }, {
      headers: { Authorization: `Bearer ${props.token}` }
    })

    emit('enabled')
    emit('close')
  } catch (e) {
    error.value = '驗證碼錯誤，請重試'
  } finally {
    loading.value = false
  }
}

// 當組件顯示時自動開始
import { watch } from 'vue'
watch(() => props.show, (newVal) => {
  if (newVal) {
    startSetup()
    code.value = ''
    error.value = ''
  }
})
</script>

<template>
  <div v-if="show" class="fixed inset-0 bg-black/80 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
    <div class="bg-gray-800 rounded-2xl shadow-2xl w-full max-w-md overflow-hidden border border-gray-700">
      
      <div class="bg-gray-900/50 p-6 flex justify-between items-center border-b border-gray-700">
        <h2 class="text-xl font-bold text-white">設定兩階段驗證 (2FA)</h2>
        <button @click="$emit('close')" class="text-gray-400 hover:text-white">✕</button>
      </div>

      <div class="p-8 space-y-6">
        
        <div v-if="error" class="bg-red-500/10 border border-red-500/50 text-red-400 px-4 py-3 rounded-lg text-sm">
          {{ error }}
        </div>

        <div class="text-center space-y-4">
          <div v-if="loading && !qrCodeUrl" class="text-gray-400">載入中...</div>
          
          <div v-else class="space-y-6">
            <div class="bg-white p-4 rounded-xl inline-block">
              <img v-if="qrCodeUrl" :src="qrCodeUrl" alt="2FA QR Code" class="w-48 h-48" />
            </div>
            
            <div class="text-left text-sm text-gray-300 space-y-2">
              <p>1. 下載 <strong>Google Authenticator</strong> App。</p>
              <p>2. 開啟 App 並掃描上方的 QR Code。</p>
              <p>3. 輸入 App 顯示的 6 位數代碼。</p>
            </div>

            <div class="pt-4">
              <input 
                v-model="code"
                type="text" 
                maxlength="6"
                class="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white text-center text-2xl tracking-widest focus:ring-2 focus:ring-blue-500 outline-none"
                placeholder="000000"
              >
            </div>

            <button 
              @click="verifySetup"
              :disabled="loading || code.length !== 6"
              class="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ loading ? '驗證中...' : '啟用 2FA' }}
            </button>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>
