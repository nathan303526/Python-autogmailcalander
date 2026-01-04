<script setup>
import { ref, onMounted } from 'vue'
import WeatherCard from './components/WeatherCard.vue'
import FoodPicker from './components/FoodPicker.vue'
import QuickLinks from './components/QuickLinks.vue'
import SmartAssistant from './components/SmartAssistant.vue'
import MultiAI from './components/MultiAI.vue'
import SchoolLinks from './components/SchoolLinks.vue'
import LoginModal from './components/LoginModal.vue'
import TwoFASetup from './components/TwoFASetup.vue'
import ProfileSettings from './components/ProfileSettings.vue'
import axios from 'axios'

const currentPage = ref('assistant') // 預設顯示智慧助理頁面
const isSidebarOpen = ref(true) // 側邊欄開關狀態
const isLoggedIn = ref(false)
const showLoginModal = ref(false)
const show2FAModal = ref(false)
const showProfileModal = ref(false)
const user = ref(null)
const token = ref(localStorage.getItem('token') || '')

const checkLogin = async () => {
  const currentToken = localStorage.getItem('token')
  token.value = currentToken || ''
  
  if (!currentToken) {
    isLoggedIn.value = false
    showLoginModal.value = true
    return
  }

  try {
    const res = await axios.get('http://localhost:8000/api/users/me', {
      headers: { Authorization: `Bearer ${currentToken}` }
    })
    user.value = res.data
    isLoggedIn.value = true
    showLoginModal.value = false
  } catch (e) {
    // Token 無效
    localStorage.removeItem('token')
    token.value = ''
    isLoggedIn.value = false
    showLoginModal.value = true
  }
}

const onLoginSuccess = (userData) => {
  user.value = userData
  token.value = localStorage.getItem('token')
  isLoggedIn.value = true
  showLoginModal.value = false
}

const handleLogout = () => {
  localStorage.removeItem('token')
  token.value = ''
  isLoggedIn.value = false
  user.value = null
  showLoginModal.value = true
}

onMounted(() => {
  checkLogin()
})
</script>

<template>
  <div class="min-h-screen bg-gray-900 text-gray-100 p-6 flex gap-6 font-sans relative">
    
    <LoginModal :show="showLoginModal" @login-success="onLoginSuccess" />
    <TwoFASetup 
      :show="show2FAModal" 
      :token="token" 
      @close="show2FAModal = false"
      @enabled="checkLogin" 
    />
    <ProfileSettings
      :show="showProfileModal"
      :user="user"
      :token="token"
      @close="showProfileModal = false"
      @update-user="checkLogin"
    />

    <!-- 側邊欄切換按鈕 (當側邊欄關閉時顯示) -->
    <button 
      v-if="!isSidebarOpen && isLoggedIn"
      @click="isSidebarOpen = true"
      class="absolute left-0 top-1/3 transform -translate-y-1/2 bg-gray-800 py-8 px-1.5 rounded-r-xl border border-l-0 border-gray-700 hover:bg-gray-700 transition z-50 shadow-xl text-gray-400 hover:text-white"
      title="打開側邊欄"
    >
      ▶
    </button>

    <!-- 左側邊欄 -->
    <aside 
      v-if="isLoggedIn"
      class="flex flex-col gap-6 transition-all duration-300 ease-in-out relative"
      :class="isSidebarOpen ? 'w-72 opacity-100 translate-x-0' : 'w-0 opacity-0 -translate-x-full overflow-hidden'"
    >
      <!-- 關閉按鈕 -->
      <button 
        v-if="isSidebarOpen"
        @click="isSidebarOpen = false"
        class="absolute -right-4 top-1/2 transform -translate-y-1/2 bg-gray-800 p-1 rounded-full border border-gray-600 hover:bg-gray-700 z-10 text-gray-400 hover:text-white w-8 h-8 flex items-center justify-center shadow-xl"
        title="收起側邊欄"
      >
        ◀
      </button>

      <WeatherCard />
      <FoodPicker />
    </aside>

    <!-- 右側主區塊 -->
    <main v-if="isLoggedIn" class="flex-1 flex flex-col min-w-0">
      <!-- 頂部列：導航 + 使用者資訊 -->
      <div class="flex justify-between items-start mb-6">
        <QuickLinks @changePage="(page) => currentPage = page" />
        
        <div @click="showProfileModal = true"
            class="bg-gray-700 hover:bg-gray-600 text-gray-300 px-3 py-1.5 rounded-lg text-xs font-medium transition"
          >
          

          <button 
             class="flex items-center gap-4 bg-gray-800 p-2 rounded-xl border border-gray-700">
          <div class="px-2 text-sm">
            <div class="text-gray-400 text-xs">Logged in as</div>
            <div class="font-bold text-blue-400">{{ user?.username }}</div>
          </div>
            設定
          </button>
          
          <button 
            v-if="!user?.['2fa_enabled']"
            @click="show2FAModal = true"
            class="bg-yellow-600/20 text-yellow-400 hover:bg-yellow-600/30 px-3 py-1.5 rounded-lg text-xs font-medium transition"
          >
            啟用 2FA
          </button>
          
          <button 
            @click="handleLogout"
            class="bg-red-600/20 text-red-400 hover:bg-red-600/30 px-3 py-1.5 rounded-lg text-xs font-medium transition"
          >
            登出
          </button>
        </div>
      </div>
      
      <!-- 內容顯示區 -->
      <div class="flex-1 transition-all duration-300">
        <SmartAssistant v-if="currentPage === 'assistant'" />
        <MultiAI v-else-if="currentPage === 'ai'" />
        <SchoolLinks v-else-if="currentPage === 'school'" />
      </div>
    </main>
  </div>
</template>

<style>
/* 自定義捲軸樣式 */
::-webkit-scrollbar {
  width: 8px;
}
::-webkit-scrollbar-track {
  background: #1f2937; 
}
::-webkit-scrollbar-thumb {
  background: #4b5563; 
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
  background: #6b7280; 
}
</style>
