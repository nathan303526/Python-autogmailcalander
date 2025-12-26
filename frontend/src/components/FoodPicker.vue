<script setup>
import { ref } from 'vue'
import axios from 'axios'
import dayjs from 'dayjs'

const food = ref(null)
const API_BASE = 'http://localhost:8000/api'

// 自動判斷時段標題
const getMealTitle = () => {
  const hour = dayjs().hour()
  if (hour >= 5 && hour < 11) return '早餐吃什麼？'
  if (hour >= 11 && hour < 17) return '午餐吃什麼？'
  if (hour >= 17 && hour < 22) return '晚餐吃什麼？'
  return '宵夜吃什麼？'
}
const mealTitle = ref(getMealTitle())

// 狀態
const selectedLocations = ref(['後門', '宵夜街'])
const onlyOpen = ref(true) // 預設只選營業中
const isRolling = ref(false)
const displayFood = ref('點擊開始')
const showOptions = ref(false) // 控制選項顯示

// 地點選項
const locations = ['後門', '山下', '宵夜街']

// 抽籤邏輯
const pickFood = async () => {
  if (isRolling.value) return
  if (selectedLocations.value.length === 0) {
    alert('請至少選擇一個地點！')
    return
  }
  
  isRolling.value = true
  food.value = null
  
  // 1. 啟動老虎機動畫
  const animationInterval = setInterval(() => {
    const tempOptions = ['🍔', '🍜', '🍱', '🍲', '🍛', '🍝', '🥩', '🍗']
    displayFood.value = tempOptions[Math.floor(Math.random() * tempOptions.length)]
  }, 100)

  try {
    // 2. 呼叫後端 API
    const res = await axios.get(`${API_BASE}/food`, {
      params: {
        locations: selectedLocations.value,
        only_open: onlyOpen.value
      },
      paramsSerializer: params => {
        const searchParams = new URLSearchParams();
        for (const key in params) {
          const val = params[key];
          if (Array.isArray(val)) {
            val.forEach(v => searchParams.append(key, v));
          } else {
            searchParams.append(key, val);
          }
        }
        return searchParams.toString();
      }
    })
    
    // 3. 延遲顯示結果
    setTimeout(() => {
      clearInterval(animationInterval)
      if (res.data.error) {
        displayFood.value = '❌ 無符合'
        food.value = { name: res.data.error }
      } else {
        food.value = res.data
        displayFood.value = res.data.food
      }
      isRolling.value = false
    }, 1500)

  } catch (error) {
    console.error('Error picking food:', error)
    clearInterval(animationInterval)
    displayFood.value = '❌ 錯誤'
    isRolling.value = false
  }
}
</script>

<template>
  <div class="bg-gray-800 p-6 rounded-2xl shadow-lg border border-gray-700 flex flex-col items-center text-center">
    <h2 
      @click="showOptions = !showOptions"
      class="text-xl font-bold mb-4 text-green-400 cursor-pointer hover:text-green-300 flex items-center gap-2 select-none"
    >
      {{ mealTitle }}
      <span class="text-sm transition-transform duration-300" :class="showOptions ? 'rotate-180' : ''">▼</span>
    </h2>
    
    <!-- 選項區 (可收折) -->
    <div v-show="showOptions" class="w-full mb-4 space-y-3 transition-all duration-300">
      <!-- 地點 Checkbox -->
      <div class="flex flex-wrap justify-center gap-4">
        <label v-for="loc in locations" :key="loc" class="flex items-center space-x-2 cursor-pointer select-none">
          <input type="checkbox" :value="loc" v-model="selectedLocations" class="w-4 h-4 text-green-600 rounded focus:ring-green-500 bg-gray-700 border-gray-600">
          <span class="text-gray-300">{{ loc }}</span>
        </label>
      </div>
      
      <!-- 營業中 Checkbox -->
      <div class="flex justify-center">
        <label class="flex items-center space-x-2 cursor-pointer select-none bg-gray-700/50 px-3 py-1 rounded-full border border-gray-600">
          <input type="checkbox" v-model="onlyOpen" class="w-4 h-4 text-blue-600 rounded focus:ring-blue-500 bg-gray-700 border-gray-600">
          <span class="text-sm text-blue-300">只顯示營業中</span>
        </label>
      </div>
    </div>

    <!-- 老虎機顯示區 -->
    <div class="mb-6 h-24 w-full bg-gray-900 rounded-xl border-2 border-gray-700 flex flex-col items-center justify-center overflow-hidden relative shadow-inner p-2">
      <div class="text-2xl font-bold transition-all duration-100 z-10"
        :class="isRolling ? 'text-gray-400 blur-[1px]' : 'text-yellow-400'"
      >
        {{ displayFood }}
      </div>
      
      <!-- 詳細資訊 (抽中後顯示) -->
      <div v-if="food && !isRolling && !food.error" class="text-xs text-gray-400 mt-1 z-10 space-y-0.5">
        <p>{{ food.location }}</p>
        <p>{{ food.address }}</p>
        <p class="text-green-500">{{ food.businesshours }}</p>
      </div>

      <!-- 裝飾線條 -->
      <div class="absolute top-0 left-0 w-full h-full bg-gradient-to-b from-black/20 via-transparent to-black/20 pointer-events-none"></div>
    </div>

    <button 
      @click="pickFood"
      :disabled="isRolling"
      class="w-full bg-green-600 hover:bg-green-500 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-bold py-3 px-4 rounded-xl transition duration-300 transform hover:scale-105 active:scale-95 shadow-md flex items-center justify-center gap-2"
    >
      <span v-if="isRolling" class="animate-spin">🎲</span>
      <span v-else>🎰</span>
      {{ isRolling ? '抽籤中...' : '開始轉動' }}
    </button>
  </div>
</template>
