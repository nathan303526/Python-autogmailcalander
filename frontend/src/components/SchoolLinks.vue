<script setup>
import { ref } from 'vue'

const links = [
  { name: 'Uedu', url: 'https://uedu.tw/', icon: '🏫', color: 'bg-blue-600' },
  { name: 'Portal 入口', url: 'https://portal.ncu.edu.tw', icon: '🔑', color: 'bg-emerald-600' },
  { name: '服學中心', url: 'https://service-learning.ncu.edu.tw/', icon: '📚', color: 'bg-orange-500' },
  { name: '圖書館', url: 'https://lib.ncu.edu.tw', icon: '📖', color: 'bg-amber-600' },
  { name: 'Hackmd', url: 'https://hackmd.io', icon: '/assets/13574138.png', color: 'bg-indigo-600' },
  { name: 'Youtube', url: 'https://www.youtube.com', icon: '/assets/youtube-icon.png', color: 'bg-red-600' },
  { name: 'Github', url: 'https://github.com', icon: '/assets/github-mark-white.png', color: 'bg-gray-800' },
  { name: 'iNCU', url: 'https://cis.ncu.edu.tw/iNCU/home', icon: '💻', color: 'bg-cyan-600' },
]
</script>

<template>
  <div class="bg-gray-800 p-6 rounded-2xl shadow-lg border border-gray-700 h-full">
    <h2 class="text-2xl font-bold mb-6 text-white flex items-center gap-2">
      <span>🏫</span> 學校資源導航
    </h2>
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <a 
        v-for="link in links" 
        :key="link.name" 
        :href="link.url" 
        target="_blank"
        class="block p-4 rounded-xl transition transform hover:scale-105 hover:shadow-xl border border-gray-600 group"
        :class="link.color"
      >
        <div class="text-3xl mb-2 flex justify-center h-10 items-center">
          <!-- 判斷是否為圖片路徑 -->
          <img 
            v-if="link.icon.includes('/') || link.icon.includes('.')" 
            :src="link.icon" 
            class="w-8 h-8 object-contain" 
            alt="icon"
          />
          <!-- 否則顯示 Emoji -->
          <span v-else>{{ link.icon }}</span>
        </div>
        <div class="font-bold text-white">{{ link.name }}</div>
      </a>
    </div>
  </div>
</template>