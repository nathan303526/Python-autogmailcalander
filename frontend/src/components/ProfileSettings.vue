<script setup>
import { ref, reactive, watch } from 'vue'
import axios from 'axios'
import { API_BASE } from '../config'

const props = defineProps({
  show: Boolean,
  user: Object,
  token: String
})

const emit = defineEmits(['close', 'update-user'])

const activeTab = ref('profile') // 'profile', 'password'
const loading = ref(false)
const message = ref('')
const error = ref('')

// Profile Form Data
const profileForm = reactive({
  full_name: '',
  email: '',
  openai_api_key: '',
  gemini_api_key: ''
})

// Password Form Data
const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

// Initialize form when modal opens or user changes
watch(() => props.show, (newVal) => {
  if (newVal && props.user) {
    profileForm.full_name = props.user.full_name || ''
    profileForm.email = props.user.email || ''
    // API keys are usually hidden, but we can let them overwrite
    profileForm.openai_api_key = '' 
    profileForm.gemini_api_key = ''
    
    // Reset password form
    passwordForm.old_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''
    
    message.value = ''
    error.value = ''
  }
})

const updateProfile = async () => {
  loading.value = true
  message.value = ''
  error.value = ''
  
  try {
    const payload = {
      full_name: profileForm.full_name,
      email: profileForm.email
    }
    
    // Only send API keys if they are provided (not empty)
    if (profileForm.openai_api_key) payload.openai_api_key = profileForm.openai_api_key
    if (profileForm.gemini_api_key) payload.gemini_api_key = profileForm.gemini_api_key
    
    await axios.put(`${API_BASE}/users/me`, payload, {
      headers: { Authorization: `Bearer ${props.token}` }
    })
    
    message.value = '個人資料已更新'
    
    // Emit event to refresh user data in parent
    emit('update-user')
    
  } catch (e) {
    error.value = e.response?.data?.detail || '更新失敗'
  } finally {
    loading.value = false
  }
}

const updatePassword = async () => {
  if (passwordForm.new_password !== passwordForm.confirm_password) {
    error.value = '新密碼與確認密碼不符'
    return
  }
  
  loading.value = true
  message.value = ''
  error.value = ''
  
  try {
    await axios.put(`${API_BASE}/users/me/password`, {
      old_password: passwordForm.old_password,
      new_password: passwordForm.new_password
    }, {
      headers: { Authorization: `Bearer ${props.token}` }
    })
    
    message.value = '密碼已更新'
    passwordForm.old_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''
    
  } catch (e) {
    error.value = e.response?.data?.detail || '密碼更新失敗'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div v-if="show" class="fixed inset-0 bg-black/70 flex items-center justify-center z-50 backdrop-blur-sm p-4">
    <div class="bg-gray-800 rounded-2xl shadow-2xl w-full max-w-md overflow-hidden border border-gray-700">
      
      <!-- Header -->
      <div class="bg-gray-900/50 p-4 border-b border-gray-700 flex justify-between items-center">
        <h2 class="text-xl font-bold text-white">帳號設定</h2>
        <button @click="$emit('close')" class="text-gray-400 hover:text-white transition">
          ✕
        </button>
      </div>
      
      <!-- Tabs -->
      <div class="flex border-b border-gray-700">
        <button 
          @click="activeTab = 'profile'"
          class="flex-1 py-3 text-sm font-medium transition relative"
          :class="activeTab === 'profile' ? 'text-blue-400' : 'text-gray-400 hover:text-gray-200'"
        >
          個人資料 & API Key
          <div v-if="activeTab === 'profile'" class="absolute bottom-0 left-0 w-full h-0.5 bg-blue-400"></div>
        </button>
        <button 
          @click="activeTab = 'password'"
          class="flex-1 py-3 text-sm font-medium transition relative"
          :class="activeTab === 'password' ? 'text-blue-400' : 'text-gray-400 hover:text-gray-200'"
        >
          修改密碼
          <div v-if="activeTab === 'password'" class="absolute bottom-0 left-0 w-full h-0.5 bg-blue-400"></div>
        </button>
      </div>

      <!-- Content -->
      <div class="p-6">
        
        <!-- Status Messages -->
        <div v-if="message" class="mb-4 p-3 bg-green-500/20 border border-green-500/50 rounded-lg text-green-200 text-sm">
          {{ message }}
        </div>
        <div v-if="error" class="mb-4 p-3 bg-red-500/20 border border-red-500/50 rounded-lg text-red-200 text-sm">
          {{ error }}
        </div>

        <!-- Profile Tab -->
        <div v-if="activeTab === 'profile'" class="space-y-4">
          <div>
            <label class="block text-xs text-gray-400 mb-1">顯示名稱</label>
            <input 
              v-model="profileForm.full_name"
              type="text" 
              class="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500 transition"
              placeholder="您的姓名"
            >
          </div>
          
          <div>
            <label class="block text-xs text-gray-400 mb-1">Email</label>
            <input 
              v-model="profileForm.email"
              type="email" 
              class="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500 transition"
              placeholder="example@email.com"
            >
          </div>
          
          <div class="pt-2 border-t border-gray-700 mt-2">
            <h3 class="text-sm font-bold text-gray-300 mb-3">API Keys (選填)</h3>
            <p class="text-xs text-gray-500 mb-3">設定後將優先使用您的 Key，若留空則不變更。</p>
            
            <div class="mb-3">
              <label class="block text-xs text-gray-400 mb-1">OpenAI API Key</label>
              <input 
                v-model="profileForm.openai_api_key"
                type="password" 
                class="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500 transition"
                placeholder="sk-..."
              >
            </div>
            
            <div>
              <label class="block text-xs text-gray-400 mb-1">Gemini API Key</label>
              <input 
                v-model="profileForm.gemini_api_key"
                type="password" 
                class="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500 transition"
                placeholder="AIza..."
              >
            </div>
          </div>

          <button 
            @click="updateProfile" 
            :disabled="loading"
            class="w-full bg-blue-600 hover:bg-blue-500 text-white py-2 rounded-lg font-medium transition mt-4 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ loading ? '儲存中...' : '儲存變更' }}
          </button>
        </div>

        <!-- Password Tab -->
        <div v-if="activeTab === 'password'" class="space-y-4">
          <div>
            <label class="block text-xs text-gray-400 mb-1">舊密碼</label>
            <input 
              v-model="passwordForm.old_password"
              type="password" 
              class="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500 transition"
            >
          </div>
          
          <div>
            <label class="block text-xs text-gray-400 mb-1">新密碼</label>
            <input 
              v-model="passwordForm.new_password"
              type="password" 
              class="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500 transition"
            >
          </div>
          
          <div>
            <label class="block text-xs text-gray-400 mb-1">確認新密碼</label>
            <input 
              v-model="passwordForm.confirm_password"
              type="password" 
              class="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500 transition"
            >
          </div>

          <button 
            @click="updatePassword" 
            :disabled="loading"
            class="w-full bg-red-600 hover:bg-red-500 text-white py-2 rounded-lg font-medium transition mt-4 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ loading ? '更新中...' : '更新密碼' }}
          </button>
        </div>

      </div>
    </div>
  </div>
</template>
