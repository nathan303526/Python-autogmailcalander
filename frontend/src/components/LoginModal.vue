<script setup>
import { ref, reactive } from 'vue'
import axios from 'axios'

const props = defineProps({
  show: Boolean
})

const emit = defineEmits(['login-success'])

const mode = ref('login') // 'login', 'register', '2fa'
const loading = ref(false)
const error = ref('')

const form = reactive({
  username: '',
  password: '',
  code: '' // 2FA code
})

// 暫存 Token，等到 2FA 通過後才真正儲存
const tempToken = ref('')

const api = axios.create({
  baseURL: 'http://localhost:8000'
})

const handleLogin = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const formData = new FormData()
    formData.append('username', form.username)
    formData.append('password', form.password)

    const res = await api.post('/api/auth/login', formData)
    const token = res.data.access_token
    
    // 取得使用者資訊，檢查是否開啟 2FA
    const userRes = await api.get('/api/users/me', {
      headers: { Authorization: `Bearer ${token}` }
    })

    if (userRes.data['2fa_enabled']) {
      // 需要 2FA
      tempToken.value = token
      mode.value = '2fa'
    } else {
      // 登入成功
      localStorage.setItem('token', token)
      emit('login-success', userRes.data)
    }
  } catch (e) {
    error.value = e.response?.data?.detail || '登入失敗'
  } finally {
    loading.value = false
  }
}

const handleRegister = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const res = await api.post('/api/auth/register', {
      username: form.username,
      password: form.password
    })
    
    // 註冊後直接登入成功 (通常註冊後還沒開啟 2FA)
    const token = res.data.access_token
    localStorage.setItem('token', token)
    
    // 取得使用者資訊
    const userRes = await api.get('/api/users/me', {
      headers: { Authorization: `Bearer ${token}` }
    })
    
    emit('login-success', userRes.data)
  } catch (e) {
    error.value = e.response?.data?.detail || '註冊失敗'
  } finally {
    loading.value = false
  }
}

const handle2FA = async () => {
  loading.value = true
  error.value = ''
  
  try {
    // 驗證 2FA
    await api.post('/api/auth/2fa/verify', {
      username: form.username,
      code: form.code
    }, {
      headers: { Authorization: `Bearer ${tempToken.value}` }
    })

    // 驗證成功，儲存 Token
    localStorage.setItem('token', tempToken.value)
    
    // 取得使用者資訊
    const userRes = await api.get('/api/users/me', {
      headers: { Authorization: `Bearer ${tempToken.value}` }
    })
    
    emit('login-success', userRes.data)
  } catch (e) {
    error.value = e.response?.data?.detail || '驗證碼錯誤'
  } finally {
    loading.value = false
  }
}

const switchMode = (newMode) => {
  mode.value = newMode
  error.value = ''
  form.code = ''
}
</script>

<template>
  <div v-if="show" class="fixed inset-0 bg-black/80 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
    <div class="bg-gray-800 rounded-2xl shadow-2xl w-full max-w-md overflow-hidden border border-gray-700">
      
      <!-- Header -->
      <div class="bg-gray-900/50 p-6 text-center border-b border-gray-700">
        <h2 class="text-2xl font-bold text-white">
          {{ mode === 'login' ? '歡迎回來' : mode === 'register' ? '建立帳號' : '二階段驗證' }}
        </h2>
        <p class="text-gray-400 text-sm mt-2">
          {{ mode === 'login' ? '請登入以繼續使用智慧助理' : mode === 'register' ? '註冊以開始使用' : '請輸入 Google Authenticator 上的 6 位數代碼' }}
        </p>
      </div>

      <!-- Body -->
      <div class="p-8 space-y-6">
        
        <!-- Error Message -->
        <div v-if="error" class="bg-red-500/10 border border-red-500/50 text-red-400 px-4 py-3 rounded-lg text-sm flex items-center gap-2">
          <span class="text-lg">⚠️</span> {{ error }}
        </div>

        <!-- Login / Register Form -->
        <form v-if="mode === 'login' || mode === 'register'" @submit.prevent="mode === 'login' ? handleLogin() : handleRegister()" class="space-y-4">
          <div>
            <label class="block text-gray-400 text-sm font-medium mb-1">帳號</label>
            <input 
              v-model="form.username"
              type="text" 
              required
              class="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
              placeholder="輸入您的帳號"
            >
          </div>
          
          <div>
            <label class="block text-gray-400 text-sm font-medium mb-1">密碼</label>
            <input 
              v-model="form.password"
              type="password" 
              required
              class="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
              placeholder="輸入您的密碼"
            >
          </div>

          <button 
            type="submit" 
            :disabled="loading"
            class="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded-lg transition transform active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ loading ? '處理中...' : (mode === 'login' ? '登入' : '註冊') }}
          </button>
        </form>

        <!-- 2FA Form -->
        <form v-if="mode === '2fa'" @submit.prevent="handle2FA" class="space-y-4">
          <div>
            <label class="block text-gray-400 text-sm font-medium mb-1">驗證碼</label>
            <input 
              v-model="form.code"
              type="text" 
              required
              maxlength="6"
              class="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white text-center text-2xl tracking-widest focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
              placeholder="000000"
            >
          </div>

          <button 
            type="submit" 
            :disabled="loading"
            class="w-full bg-green-600 hover:bg-green-500 text-white font-bold py-3 rounded-lg transition transform active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ loading ? '驗證中...' : '確認' }}
          </button>
          
          <button 
            type="button"
            @click="switchMode('login')"
            class="w-full text-gray-400 hover:text-white text-sm"
          >
            返回登入
          </button>
        </form>

        <!-- Footer Links -->
        <div v-if="mode !== '2fa'" class="text-center pt-2">
          <p v-if="mode === 'login'" class="text-gray-400 text-sm">
            還沒有帳號？ 
            <button @click="switchMode('register')" class="text-blue-400 hover:text-blue-300 font-medium">立即註冊</button>
          </p>
          <p v-if="mode === 'register'" class="text-gray-400 text-sm">
            已有帳號？ 
            <button @click="switchMode('login')" class="text-blue-400 hover:text-blue-300 font-medium">登入</button>
          </p>
        </div>

      </div>
    </div>
  </div>
</template>
