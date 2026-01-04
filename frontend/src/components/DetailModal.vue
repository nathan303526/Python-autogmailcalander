<script setup>
import { computed, ref } from 'vue'
import axios from 'axios'
import { API_BASE } from '../config'

const props = defineProps({
  item: {
    type: Object,
    required: true
  },
  type: {
    type: String,
    required: true // 'gmail' or 'calendar'
  }
})

const emit = defineEmits(['close', 'deleted'])

const isDeleting = ref(false)

const deleteEvent = async () => {
  console.log('Event item:', props.item)
  console.log('Event ID:', props.item.id)
  
  if (!confirm('確定要刪除這個行程嗎？')) return
  
  isDeleting.value = true
  try {
    await axios.delete(`${API_BASE}/calendar/delete-event/${props.item.id}`)
    alert('已成功刪除行程')
    emit('deleted')
    emit('close')
  } catch (error) {
    console.error('Delete error:', error)
    alert('刪除失敗：' + (error.response?.data?.detail || error.message))
  } finally {
    isDeleting.value = false
  }
}

const title = computed(() => {
  return props.type === 'gmail' ? props.item.subject : props.item.summary
})

const dateInfo = computed(() => {
  if (props.type === 'gmail') {
    // 假設後端回傳的格式包含 date 欄位，如果沒有可能需要調整
    return props.item.date || '未知日期' 
  } else {
    // Calendar
    const start = new Date(props.item.start).toLocaleString('zh-TW', { hour12: false })
    const end = props.item.end ? new Date(props.item.end).toLocaleString('zh-TW', { hour12: false }) : ''
    return `${start} ${end ? ' - ' + end : ''}`
  }
})

const content = computed(() => {
  return props.type === 'gmail' 
    ? (props.item.snippet || props.item.body || '無內容') 
    : (props.item.description || '無詳細描述')
})

const subHeader = computed(() => {
    return props.type === 'gmail' 
      ? `寄件者: ${props.item.sender}` 
      : (props.item.location ? `地點: ${props.item.location}` : '')
})

const headerColor = computed(() => {
    return props.type === 'gmail' ? 'bg-blue-900' : 'bg-blue-600'
})

const icon = computed(() => {
    return props.type === 'gmail' ? '📧' : '📅'
})
</script>

<template>
  <div class="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4 backdrop-blur-sm" @click.self="$emit('close')">
    <div class="bg-gray-800 rounded-2xl shadow-2xl w-full max-w-2xl overflow-hidden border border-gray-600 flex flex-col max-h-[85vh] animate-fade-in-up">
      <!-- Header -->
      <div :class="[headerColor, 'p-6 flex justify-between items-start shadow-md']">
        <div class="flex gap-4 items-start">
            <div class="text-4xl bg-white/20 p-2 rounded-lg backdrop-blur-sm">{{ icon }}</div>
            <div>
                <h2 class="text-2xl font-bold text-white leading-tight">{{ title }}</h2>
                <div class="text-white/90 mt-2 text-sm font-medium flex items-center gap-2">
                  <span class="opacity-75">🕒</span> {{ dateInfo }}
                </div>
                <div v-if="subHeader" class="text-white/90 mt-1 text-sm flex items-center gap-2">
                  <span class="opacity-75">📍</span> {{ subHeader }}
                </div>
            </div>
        </div>
        <button @click="$emit('close')" class="text-white/70 hover:text-white hover:bg-white/20 rounded-full p-1 transition text-2xl leading-none w-8 h-8 flex items-center justify-center">&times;</button>
      </div>

      <!-- Body -->
      <div class="p-8 overflow-y-auto text-gray-300 leading-relaxed whitespace-pre-wrap text-lg bg-gray-800 custom-scrollbar">
        {{ content }}
      </div>

      <!-- Footer -->
      <div class="p-4 border-t border-gray-700 bg-gray-900/50 flex justify-between gap-3">
        <button 
          v-if="type === 'calendar'"
          @click="deleteEvent" 
          :disabled="isDeleting || !item.id"
          class="px-6 py-2 bg-red-600 hover:bg-red-500 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition font-medium flex items-center gap-2"
        >
          <span v-if="isDeleting" class="animate-spin">⏳</span>
          <span v-if="!item.id" class="text-xs">(無法刪除：缺少 ID)</span>
          <span v-else>{{ isDeleting ? '刪除中...' : '刪除行程' }}</span>
        </button>
        <div v-else></div>
        <button @click="$emit('close')" class="px-6 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition font-medium border border-gray-600">
          關閉
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.animate-fade-in-up {
  animation: fadeInUp 0.3s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.custom-scrollbar::-webkit-scrollbar {
  width: 8px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: rgba(31, 41, 55, 0.5);
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(75, 85, 99, 0.8);
  border-radius: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(107, 114, 128, 1);
}
</style>