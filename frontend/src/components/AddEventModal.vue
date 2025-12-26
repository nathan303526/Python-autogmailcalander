<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const props = defineProps({
  email: {
    type: Object,
    required: true
  },
  date: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['close', 'added'])

const API_BASE = 'http://localhost:8000/api'
const isSubmitting = ref(false)

// 表單資料
const eventTitle = ref('')
const eventDate = ref('')
const eventTime = ref('09:00')
const eventDescription = ref('')

onMounted(() => {
  // 預填資料
  eventTitle.value = props.email.subject || ''
  eventDate.value = props.date
  eventDescription.value = `來自郵件：${props.email.sender}\n\n${props.email.snippet}`
})

const formattedDate = computed(() => {
  const date = new Date(props.date)
  return date.toLocaleDateString('zh-TW', { year: 'numeric', month: 'long', day: 'numeric' })
})

const addToCalendar = async () => {
  if (!eventTitle.value || !eventDate.value) {
    alert('請填寫標題和日期')
    return
  }

  isSubmitting.value = true

  try {
    // 組合日期和時間
    const startDateTime = `${eventDate.value}T${eventTime.value}:00`

    const response = await axios.post(`${API_BASE}/calendar/add-event`, {
      summary: eventTitle.value,
      start: startDateTime,
      description: eventDescription.value
    })

    if (response.data.success) {
      alert('已成功添加到 Google Calendar！')
      emit('added')
      emit('close')
    }
  } catch (error) {
    console.error('Add event error:', error)
    alert('添加失敗：' + (error.response?.data?.detail || error.message))
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4 backdrop-blur-sm" @click.self="$emit('close')">
    <div class="bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden border border-gray-600 flex flex-col max-h-[85vh] animate-fade-in-up">
      <!-- Header -->
      <div class="bg-gradient-to-r from-blue-600 to-blue-500 p-6 flex justify-between items-start shadow-md">
        <div>
          <h2 class="text-2xl font-bold text-white leading-tight flex items-center gap-2">
            <span>📅</span> 添加到行事曆
          </h2>
          <div class="text-white/90 mt-2 text-sm">
            {{ formattedDate }}
          </div>
        </div>
        <button @click="$emit('close')" class="text-white/70 hover:text-white hover:bg-white/20 rounded-full p-1 transition text-2xl leading-none w-8 h-8 flex items-center justify-center">&times;</button>
      </div>

      <!-- Body -->
      <div class="p-6 overflow-y-auto custom-scrollbar flex-1">
        <div class="space-y-4">
          <!-- 標題 -->
          <div>
            <label class="block text-gray-300 text-sm font-medium mb-2">活動標題 *</label>
            <input 
              v-model="eventTitle" 
              type="text" 
              class="w-full bg-gray-700 border border-gray-600 rounded-lg p-3 text-white focus:border-blue-500 focus:ring-2 focus:ring-blue-500/50 outline-none transition"
              placeholder="請輸入活動標題"
            >
          </div>

          <!-- 日期與時間 -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-gray-300 text-sm font-medium mb-2">日期 *</label>
              <input 
                v-model="eventDate" 
                type="date" 
                class="w-full bg-gray-700 border border-gray-600 rounded-lg p-3 text-white focus:border-blue-500 focus:ring-2 focus:ring-blue-500/50 outline-none transition"
              >
            </div>
            <div>
              <label class="block text-gray-300 text-sm font-medium mb-2">時間</label>
              <input 
                v-model="eventTime" 
                type="time" 
                class="w-full bg-gray-700 border border-gray-600 rounded-lg p-3 text-white focus:border-blue-500 focus:ring-2 focus:ring-blue-500/50 outline-none transition"
              >
            </div>
          </div>

          <!-- 描述 -->
          <div>
            <label class="block text-gray-300 text-sm font-medium mb-2">描述</label>
            <textarea 
              v-model="eventDescription" 
              rows="6"
              class="w-full bg-gray-700 border border-gray-600 rounded-lg p-3 text-white focus:border-blue-500 focus:ring-2 focus:ring-blue-500/50 outline-none transition resize-none"
              placeholder="請輸入活動描述"
            ></textarea>
          </div>

          <!-- 原始郵件資訊 -->
          <div class="bg-gray-700/50 rounded-lg p-4 border border-gray-600">
            <div class="text-gray-400 text-xs mb-2">📧 原始郵件</div>
            <div class="text-white text-sm font-medium truncate">{{ email.subject }}</div>
            <div class="text-gray-400 text-xs mt-1">{{ email.sender }}</div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="p-4 border-t border-gray-700 bg-gray-900/50 flex justify-end gap-3">
        <button 
          @click="$emit('close')" 
          class="px-6 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition font-medium border border-gray-600"
        >
          取消
        </button>
        <button 
          @click="addToCalendar"
          :disabled="isSubmitting || !eventTitle || !eventDate"
          class="px-6 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition font-medium shadow-lg flex items-center gap-2"
        >
          <span v-if="isSubmitting" class="animate-spin">⏳</span>
          {{ isSubmitting ? '添加中...' : '確定添加' }}
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