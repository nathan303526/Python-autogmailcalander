<script setup>
import TaskSync from './TaskSync.vue'
</script>

<template>
  <div class="h-full flex flex-col gap-6">
    <!-- Gmail 區塊 -->
    <div class="bg-gray-800 p-6 rounded-2xl shadow-lg border border-gray-700 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <div class="bg-red-600 p-3 rounded-full">
          <span class="text-2xl text-white">📧</span>
        </div>
        <div>
          <h2 class="text-xl font-bold text-white">Gmail</h2>
          <p class="text-gray-400 text-sm">查看郵件並同步待辦事項</p>
        </div>
      </div>
      <a 
        href="https://mail.google.com" 
        target="_blank"
        class="bg-white text-red-600 hover:bg-gray-100 px-6 py-2 rounded-lg font-bold transition"
      >
        前往信箱
      </a>
    </div>

    <!-- 智慧待辦助理 (TaskSync) -->
    <div class="flex-1">
      <TaskSync />
    </div>
  </div>
</template>