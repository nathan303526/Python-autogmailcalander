<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { API_BASE } from '../config'

const weather = ref(null)

const fetchWeather = async () => {
  const callWeatherApi = async (lat = null, lon = null) => {
    try {
      const params = (lat && lon) ? { lat, lon } : {}
      const res = await axios.get(`${API_BASE}/weather`, { params })
      weather.value = res.data
    } catch (err) {
      console.error('API 連線失敗:', err)
      weather.value = {
        location: "連線錯誤",
        temperature: "--",
        status: "Error",
        description: "無法連線到後端伺服器"
      }
    }
  }

  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords
        await callWeatherApi(latitude, longitude)
      },
      async (error) => {
        console.warn('定位失敗或被拒絕:', error.message)
        await callWeatherApi()
      },
      { timeout: 5000, maximumAge: 0 }
    )
  } else {
    await callWeatherApi()
  }
}

onMounted(() => {
  fetchWeather()
})
</script>

<template>
  <div class="bg-gray-800 p-6 rounded-2xl shadow-lg border border-gray-700">
    <h2 class="text-xl font-bold mb-4 text-blue-400">今日天氣</h2>
    <div v-if="weather" class="space-y-2">
      <div class="text-4xl mb-2">☁️</div>
      <div class="text-2xl font-semibold">{{ weather.location }}</div>
      <div class="text-5xl font-bold text-white">{{ weather.temperature }}°C</div>
      <div class="text-gray-400">{{ weather.status }}</div>
      <div class="text-sm text-gray-500 mt-2">{{ weather.description }}</div>
    </div>
    <div v-else class="animate-pulse flex space-x-4">
      <div class="flex-1 space-y-4 py-1">
        <div class="h-4 bg-gray-700 rounded w-3/4"></div>
        <div class="space-y-2">
          <div class="h-4 bg-gray-700 rounded"></div>
          <div class="h-4 bg-gray-700 rounded w-5/6"></div>
        </div>
      </div>
    </div>
  </div>
</template>
