<script setup>
import { ref } from 'vue'
import WeatherCard from './components/WeatherCard.vue'
import FoodPicker from './components/FoodPicker.vue'
import QuickLinks from './components/QuickLinks.vue'
import SmartAssistant from './components/SmartAssistant.vue'
import MultiAI from './components/MultiAI.vue'
import SchoolLinks from './components/SchoolLinks.vue'

const currentPage = ref('assistant') // 預設顯示智慧助理頁面
const isSidebarOpen = ref(true) // 側邊欄開關狀態
</script>

<template>
  <div class="min-h-screen bg-gray-900 text-gray-100 p-6 flex gap-6 font-sans relative">
    
    <!-- 側邊欄切換按鈕 (當側邊欄關閉時顯示) -->
    <button 
      v-if="!isSidebarOpen"
      @click="isSidebarOpen = true"
      class="absolute left-0 top-1/3 transform -translate-y-1/2 bg-gray-800 py-8 px-1.5 rounded-r-xl border border-l-0 border-gray-700 hover:bg-gray-700 transition z-50 shadow-xl text-gray-400 hover:text-white"
      title="打開側邊欄"
    >
      ▶
    </button>

    <!-- 左側邊欄 -->
    <aside 
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
    <main class="flex-1 flex flex-col min-w-0">
      <!-- 導航選單 (原 QuickLinks) -->
      <QuickLinks @changePage="(page) => currentPage = page" />
      
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
