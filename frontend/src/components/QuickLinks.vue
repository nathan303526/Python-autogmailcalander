<script setup>
const emit = defineEmits(['changePage'])

const pages = [
  { id: 'assistant', name: '智慧待辦助理', icon: '📧', desc: 'Gmail + AI 任務同步' },
  { id: 'ai', name: '多模組 AI', icon: '🤖', desc: '同時使用多個 AI 模型' },
  { id: 'school', name: '學校資源', icon: '🏫', desc: '校園常用連結導航' },
]
</script>

<template>
  <div class="grid grid-cols-3 gap-4 mb-6">
    <button 
      v-for="page in pages" 
      :key="page.id"
      @click="emit('changePage', page.id)"
      class="bg-gray-800 hover:bg-gray-700 p-4 rounded-xl flex flex-col items-center justify-center gap-2 transition border border-gray-700 group text-center h-32"
    >
      <span class="text-4xl group-hover:scale-110 transition mb-1">{{ page.icon }}</span>
      <span class="font-bold text-white text-lg">{{ page.name }}</span>
      <span class="text-xs text-gray-400">{{ page.desc }}</span>
    </button>
  </div>
</template>
