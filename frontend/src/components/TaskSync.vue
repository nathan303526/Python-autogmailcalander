<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import DetailModal from './DetailModal.vue'
import AddEventModal from './AddEventModal.vue'
import SmartAnalysis from './SmartAnalysis.vue'

const tasks = ref({ gmail: [], calendar: [] })
const calendarNextPageToken = ref('')
const isLoading = ref(false)
const isLoadingMore = ref(false)
const API_BASE = 'http://localhost:8000/api'

// Modal State
const selectedItem = ref(null)
const selectedType = ref('')
const showSmartAnalysis = ref(false)

const openDetail = (item, type) => {
  selectedItem.value = item
  selectedType.value = type
}

const closeDetail = () => {
  selectedItem.value = null
}

const openSmartAnalysis = () => {
  showSmartAnalysis.value = true
}

const closeSmartAnalysis = () => {
  showSmartAnalysis.value = false
}

// Drag and Drop State
const draggedEmail = ref(null)
const showAddEventModal = ref(false)
const dropTargetDate = ref('')
const isDragging = ref(false)
const dragOverCell = ref(null)

const startDrag = (event, email) => {
  console.log('開始拖曳:', email.subject)
  draggedEmail.value = email
  isDragging.value = true
  event.dataTransfer.effectAllowed = 'copy'
  event.dataTransfer.setData('text/plain', email.subject)
}

const onDragOver = (event, dateStr) => {
  event.preventDefault()
  event.dataTransfer.dropEffect = 'copy'
  dragOverCell.value = dateStr
}

const onDragLeave = () => {
  dragOverCell.value = null
}

const onDrop = (event, dateStr) => {
  event.preventDefault()
  console.log('放下郵件到:', dateStr)
  dragOverCell.value = null
  
  if (draggedEmail.value && dateStr) {
    dropTargetDate.value = dateStr
    showAddEventModal.value = true
    console.log('顯示彈窗')
  }
}

const onDragEnd = () => {
  console.log('拖曳結束')
  isDragging.value = false
  dragOverCell.value = null
}

const closeAddEventModal = () => {
  showAddEventModal.value = false
  dropTargetDate.value = ''
  draggedEmail.value = null
}

// Calendar View State
const currentYear = ref(new Date().getFullYear())
const currentMonth = ref(new Date().getMonth()) // 0-11

const monthNames = ["一月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "十一月", "十二月"]
const weekDays = ["日", "一", "二", "三", "四", "五", "六"]

// 計算當月日曆網格
const calendarGrid = computed(() => {
  const year = currentYear.value
  const month = currentMonth.value
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  
  const daysInMonth = lastDay.getDate()
  const startDayOfWeek = firstDay.getDay() // 0 (Sun) - 6 (Sat)
  
  const days = []
  
  // 補前一個月的空白
  for (let i = 0; i < startDayOfWeek; i++) {
    days.push({ date: null, week: Math.floor(days.length / 7) })
  }
  
  // 當月日期
  for (let i = 1; i <= daysInMonth; i++) {
    const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(i).padStart(2, '0')}`
    days.push({ 
      date: i, 
      fullDate: dateStr,
      isToday: isToday(year, month, i),
      week: Math.floor(days.length / 7)
    })
  }
  
  return days
})

// 計算每週的最大事件數量，用於動態調整行高
const weekMaxEvents = computed(() => {
  const maxEvents = {}
  calendarGrid.value.forEach(day => {
    if (day.date) {
      const events = getEventsForDay(day.fullDate)
      const week = day.week
      maxEvents[week] = Math.max(maxEvents[week] || 0, events.length)
    }
  })
  return maxEvents
})

// 計算每週的行高
const getWeekRowHeight = (week) => {
  const maxCount = weekMaxEvents.value[week] || 0
  const baseHeight = 30 // 日期數字高度
  const eventHeight = 18 // 每個事件的高度（調整為18px，讓跨天事件更緊湊）
  const minHeight = 90 // 最小高度
  return Math.max(minHeight, baseHeight + maxCount * eventHeight + 10)
}

const isToday = (year, month, day) => {
  const today = new Date()
  return today.getFullYear() === year && today.getMonth() === month && today.getDate() === day
}

const getEventsForDay = (dateStr) => {
  if (!dateStr || !tasks.value.calendar) return []
  
  // 將當前格子日期轉為 Date 物件 (00:00:00)
  const cellDate = new Date(dateStr)
  // 確保比較時不受時間影響，只比對日期部分
  const cellTime = cellDate.getTime()
  
  return tasks.value.calendar.filter(e => {
    if (!e.start) return false
    
    // 處理開始時間
    const startDateStr = e.start.split('T')[0]
    const startDate = new Date(startDateStr)
    
    // 處理結束時間 (如果沒有 end，預設為 start)
    let endDateStr = e.end ? e.end.split('T')[0] : startDateStr
    let endDate = new Date(endDateStr)
    
    // Google Calendar 全天事件的 end 是 exclusive (隔天 00:00)
    // 非全天事件 (dateTime) 如果跨天，end 也是具體時間
    // 為了簡化，我們檢查 cellDate 是否在 [startDate, endDate) 區間
    // 或者如果是單日事件，startDate == cellDate
    
    // 如果是全天事件 (沒有 'T')
    const isAllDay = !e.start.includes('T')
    
    if (isAllDay) {
      // 全天事件：包含 start，不包含 end
      // 例如 12/25 - 12/26 => 只有 12/25
      // 例如 12/25 - 12/27 => 12/25, 12/26
      return cellTime >= startDate.getTime() && cellTime < endDate.getTime()
    } else {
      // 時間事件
      // 如果是同一天：start == cell
      if (startDateStr === endDateStr) {
        return startDateStr === dateStr
      }
      
      // 跨天時間事件
      // 簡單判定：只要日期有重疊就算
      // 嚴謹判定：事件結束時間必須大於當天 00:00，事件開始時間必須小於隔天 00:00
      const nextDayTime = cellTime + 86400000 // +1 day
      
      const evtStart = new Date(e.start).getTime()
      const evtEnd = e.end ? new Date(e.end).getTime() : evtStart
      
      return evtStart < nextDayTime && evtEnd > cellTime
    }
  }).map(e => {
    // 附加樣式資訊給前端渲染使用
    const startDateStr = e.start.split('T')[0]
    let endDateStr = e.end ? e.end.split('T')[0] : startDateStr
    
    // 修正全天事件的顯示結束日期 (因為 end 是 exclusive)
    if (!e.start.includes('T')) {
        const endD = new Date(endDateStr)
        endD.setDate(endD.getDate() - 1)
        endDateStr = endD.toISOString().split('T')[0]
    }
    
    const isMultiDay = startDateStr !== endDateStr
    const isAllDay = !e.start.includes('T')
    
    // 判斷顯示樣式：全天或跨天顯示為實心條 (Solid)，單日時間事件顯示為點+文字 (Dot)
    const isSolid = isAllDay || isMultiDay
    
    // 格式化時間字串 (僅針對非全天事件)
    let timeStr = ''
    if (!isAllDay) {
        const dateObj = new Date(e.start)
        const hours = dateObj.getHours()
        const minutes = dateObj.getMinutes()
        const period = hours >= 12 ? '下午' : '上午'
        const displayHours = hours > 12 ? hours - 12 : hours
        timeStr = `${period}${displayHours}:${minutes.toString().padStart(2, '0')}`
    }

    return {
      ...e,
      isStart: startDateStr === dateStr,
      isEnd: endDateStr === dateStr,
      isMultiDay,
      isSolid,
      timeStr
    }
  }).sort((a, b) => {
    // 優先排序：跨天活動在上方，單日活動在下方
    if (a.isMultiDay && !b.isMultiDay) return -1
    if (!a.isMultiDay && b.isMultiDay) return 1
    
    // 同類型活動按開始時間排序
    const aTime = new Date(a.start).getTime()
    const bTime = new Date(b.start).getTime()
    return aTime - bTime
  })
}

const changeMonth = (delta) => {
  let newMonth = currentMonth.value + delta
  let newYear = currentYear.value
  
  if (newMonth > 11) {
    newMonth = 0
    newYear++
  } else if (newMonth < 0) {
    newMonth = 11
    newYear--
  }
  
  currentMonth.value = newMonth
  currentYear.value = newYear
  syncTasks() // 切換月份時重新同步
}

// 計算跨天活動的樣式
const getMultiDayStyle = (event, dayOfWeek) => {
  if (!event.isSolid || !event.isMultiDay) return {}
  
  const styles = {}
  
  if (event.isStart) {
    // 起始日：延伸到右邊界
    styles.marginRight = '-5px'
    styles.paddingRight = '6px'
  } else if (event.isEnd) {
    // 結束日：從左邊界延伸進來
    styles.marginLeft = '-5px'
    styles.paddingLeft = '6px'
  } else {
    // 中間日：兩邊都延伸
    styles.marginLeft = '-5px'
    styles.marginRight = '-5px'
    styles.paddingLeft = '6px'
    styles.paddingRight = '6px'
  }
  
  return styles
}

// Google 整合相關狀態
const isConfigured = ref(false)
const clientId = ref('')
const clientSecret = ref('')
const authUrl = ref('')
const authCode = ref('')
const showAuthInput = ref(false)

// 檢查後端是否已設定憑證
const checkGoogleStatus = async () => {
  try {
    const res = await axios.get(`${API_BASE}/google/status`)
    isConfigured.value = res.data.authenticated
    
    // 只有在已授權且沒有暫存資料時才自動同步
    if (isConfigured.value && (!tasks.value.gmail || tasks.value.gmail.length === 0) && (!tasks.value.calendar || tasks.value.calendar.length === 0)) {
      syncTasks()
    }
  } catch (error) {
    console.error('Status check failed', error)
  }
}

// 儲存憑證並取得授權連結
const saveCredentials = async () => {
  if (!clientId.value || !clientSecret.value) {
    alert('請輸入 Client ID 和 Client Secret')
    return
  }

  try {
    // 暫存 Client ID 到 localStorage（方便下次使用）
    localStorage.setItem('google_client_id', clientId.value)
    
    const res = await axios.post(`${API_BASE}/google/setup`, {
      client_id: clientId.value,
      client_secret: clientSecret.value
    })
    
    if (res.data.auth_url) {
      authUrl.value = res.data.auth_url
      showAuthInput.value = true
      // 自動開啟授權頁面
      window.open(res.data.auth_url, '_blank')
    }
  } catch (error) {
    alert('設定失敗: ' + (error.response?.data?.detail || error.message))
  }
}

// 送出授權碼以取得 Token
const submitAuthCode = async () => {
  if (!authCode.value) return

  try {
    await axios.post(`${API_BASE}/google/callback`, { code: authCode.value })
    isConfigured.value = true
    showAuthInput.value = false
    alert('授權成功！')
    syncTasks() // 自動開始同步
  } catch (error) {
    alert('授權失敗: ' + (error.response?.data?.detail || error.message))
  }
}

onMounted(() => {
  // 從 localStorage 讀取暫存的 ID (方便測試)
  const storedId = localStorage.getItem('google_client_id')
  if (storedId) clientId.value = storedId
  
  // 讀取暫存的資料
  const cachedData = localStorage.getItem('synced_tasks')
  if (cachedData) {
    try {
      const parsed = JSON.parse(cachedData)
      tasks.value = parsed
      calendarNextPageToken.value = parsed.calendarNextPageToken || ''
    } catch (e) {
      console.error('Failed to load cached tasks', e)
    }
  }
  
  checkGoogleStatus()
})

const syncTasks = async () => {
  isLoading.value = true
  try {
    // 傳遞當前年份和月份給後端
    const res = await axios.get(`${API_BASE}/sync-tasks`, {
      params: {
        year: currentYear.value,
        month: currentMonth.value + 1 // JS month is 0-indexed, API expects 1-12
      }
    })
    tasks.value = res.data
    calendarNextPageToken.value = res.data.calendarNextPageToken
    
    // 儲存到 localStorage
    localStorage.setItem('synced_tasks', JSON.stringify(res.data))
  } catch (error) {
    console.error('Error syncing tasks:', error)
    if (error.response && error.response.status === 401) {
      isConfigured.value = false
      alert('授權已過期或失效，請重新連結 Google 帳號')
    } else {
      alert('同步失敗，請稍後再試')
    }
  } finally {
    isLoading.value = false
  }
}

const loadMoreCalendar = async () => {
  if (!calendarNextPageToken.value) return
  
  isLoadingMore.value = true
  try {
    const res = await axios.post(`${API_BASE}/calendar/load-more`, {
      pageToken: calendarNextPageToken.value
    })
    
    // 追加資料
    if (tasks.value.calendar) {
      tasks.value.calendar.push(...res.data.calendar)
    }
    calendarNextPageToken.value = res.data.calendarNextPageToken
    
    // 更新 localStorage
    const currentData = JSON.parse(localStorage.getItem('synced_tasks') || '{}')
    currentData.calendar = tasks.value.calendar
    currentData.calendarNextPageToken = calendarNextPageToken.value
    localStorage.setItem('synced_tasks', JSON.stringify(currentData))
    
  } catch (error) {
    console.error('Error loading more calendar events:', error)
    if (error.response && error.response.status === 401) {
      isConfigured.value = false
      alert('授權已過期或失效，請重新連結 Google 帳號')
    } else {
      alert('載入更多失敗')
    }
  } finally {
    isLoadingMore.value = false
  }
}
</script>

<template>
  <div class="bg-gray-800 flex-1 rounded-2xl p-8 shadow-lg border border-gray-700 flex flex-col h-[85vh] overflow-hidden relative">
    <div class="flex justify-between items-center mb-6 flex-shrink-0">
      <div>
        <h1 class="text-3xl font-bold text-white mb-2">智慧待辦助理</h1>
        <p class="text-gray-400">AI 自動分析您的 Gmail 與 Calendar，生成最佳行動建議。</p>
      </div>
      <div class="flex gap-3">
        <button 
          @click="openSmartAnalysis"
          :disabled="!isConfigured"
          class="bg-purple-600 hover:bg-purple-500 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-bold py-3 px-6 rounded-xl transition duration-300 flex items-center gap-2 shadow-lg"
        >
          智慧分析
        </button>
        <button 
          @click="syncTasks"
          :disabled="isLoading || !isConfigured"
          class="bg-blue-600 hover:bg-blue-500 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-bold py-3 px-8 rounded-xl transition duration-300 flex items-center gap-2 shadow-lg"
        >
          <span v-if="isLoading" class="animate-spin">⏳</span>
          <span v-else>⚡</span>
          {{ isLoading ? '同步中...' : '同步 Gmail & Calendar' }}
        </button>
      </div>
    </div>

    <!-- Google 憑證設定區 (未設定時顯示) -->
    <div v-if="!isConfigured" class="mb-8 p-6 bg-gray-700/30 rounded-xl border border-dashed border-gray-500 overflow-y-auto">
      <div class="flex flex-col items-center text-center max-w-2xl mx-auto">
        <div class="text-4xl mb-3">🔐</div>
        <h2 class="text-xl font-bold text-white mb-2">連結 Google 帳號</h2>
        <p class="text-gray-300 mb-6">
          請輸入您的 Google OAuth 憑證以授權存取 Gmail 和 Calendar。
        </p>
        
        <div v-if="!showAuthInput" class="w-full space-y-4 text-left">
          <div>
            <label class="block text-gray-400 text-sm mb-1">Client ID</label>
            <input v-model="clientId" type="text" class="w-full bg-gray-800 border border-gray-600 rounded-lg p-3 text-white focus:border-blue-500 outline-none" placeholder="請輸入 Client ID">
          </div>
          <div>
            <label class="block text-gray-400 text-sm mb-1">Client Secret</label>
            <input v-model="clientSecret" type="password" class="w-full bg-gray-800 border border-gray-600 rounded-lg p-3 text-white focus:border-blue-500 outline-none" placeholder="請輸入 Client Secret">
          </div>
          <button @click="saveCredentials" class="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded-lg transition">
            取得授權連結
          </button>
        </div>

        <div v-else class="w-full space-y-4 text-left">
          <div class="bg-blue-900/30 p-4 rounded-lg border border-blue-800 text-sm text-blue-200 mb-4">
            請在新開啟的視窗中登入 Google 帳號，並將顯示的「授權碼 (Authorization Code)」貼在下方。
            <br>
            <a :href="authUrl" target="_blank" class="underline font-bold mt-2 block">如果視窗沒有開啟，請點此連結</a>
          </div>
          <div>
            <label class="block text-gray-400 text-sm mb-1">授權碼 (Authorization Code)</label>
            <input v-model="authCode" type="text" class="w-full bg-gray-800 border border-gray-600 rounded-lg p-3 text-white focus:border-blue-500 outline-none" placeholder="請貼上授權碼">
          </div>
          <button @click="submitAuthCode" class="w-full bg-green-600 hover:bg-green-500 text-white font-bold py-3 rounded-lg transition">
            驗證並連線
          </button>
        </div>
      </div>
    </div>

    <!-- 列表顯示區 (Flex 佈局) -->
    <div v-else class="flex-1 flex gap-6 overflow-hidden min-h-0">
      <!-- Gmail 區塊 (左側，可滾動) -->
      <div class="w-1/3 bg-gray-700/30 rounded-xl p-4 flex flex-col overflow-hidden border border-gray-600">
        <h3 class="text-xl font-bold text-white mb-4 flex items-center gap-2 flex-shrink-0">
          <span class="text-red-400">📧</span> Gmail (最新 20 封)
        </h3>
        <div class="flex-1 overflow-y-auto space-y-3 pr-2 custom-scrollbar">
          <div v-if="tasks.gmail && tasks.gmail.length === 0" class="text-gray-500 text-center mt-10">無新郵件</div>
          <div 
            v-for="(mail, idx) in tasks.gmail" 
            :key="idx" 
            draggable="true"
            @dragstart="startDrag($event, mail)"
            @dragend="onDragEnd"
            @click="openDetail(mail, 'gmail')"
            class="bg-gray-800 p-3 rounded-lg border border-gray-700 hover:bg-gray-600 transition cursor-move group"
          >
            <div class="font-bold text-white truncate group-hover:text-blue-300 transition">{{ mail.subject }}</div>
            <div class="text-xs text-gray-400 mt-1">{{ mail.sender }}</div>
            <div class="text-sm text-gray-300 mt-2 line-clamp-2">{{ mail.snippet }}</div>
          </div>
        </div>
      </div>

      <!-- Calendar 區塊 (右側，月曆視圖) -->
      <div class="w-2/3 bg-gray-700/30 rounded-xl p-4 flex flex-col overflow-hidden border border-gray-600">
        <div class="flex justify-between items-center mb-4 flex-shrink-0">
          <h3 class="text-xl font-bold text-white flex items-center gap-2">
            <span class="text-blue-400">📅</span> {{ currentYear }}年 {{ monthNames[currentMonth] }}
          </h3>
          <div class="flex gap-2">
            <button @click="changeMonth(-1)" class="p-2 bg-gray-600 hover:bg-gray-500 rounded-lg text-white transition">◀</button>
            <button @click="changeMonth(1)" class="p-2 bg-gray-600 hover:bg-gray-500 rounded-lg text-white transition">▶</button>
          </div>
        </div>
        
        <!-- Calendar Grid -->
        <div class="flex-1 flex flex-col min-h-0">
          <!-- Weekday Headers -->
          <div class="grid grid-cols-7 gap-1 mb-1 text-center">
            <div v-for="day in weekDays" :key="day" class="text-gray-400 text-sm font-bold py-1">
              {{ day }}
            </div>
          </div>
          
          <!-- Days Grid -->
          <div class="flex flex-col flex-1 overflow-y-auto custom-scrollbar border border-gray-700">
            <div 
              v-for="week in Math.ceil(calendarGrid.length / 7)" 
              :key="week"
              class="grid grid-cols-7 gap-0"
              :style="{ height: getWeekRowHeight(week - 1) + 'px' }"
            >
              <div 
                v-for="(day, idx) in calendarGrid.slice((week - 1) * 7, week * 7)" 
                :key="idx" 
                @dragover="day.date ? onDragOver($event, day.fullDate) : null"
                @dragleave="onDragLeave"
                @drop="day.date ? onDrop($event, day.fullDate) : null"
                class="bg-gray-800 flex flex-col relative overflow-hidden border transition-all"
                :class="{ 
                  'bg-gray-900/50': !day.date, 
                  'bg-blue-900/10': day.isToday,
                  'border-gray-700/50': dragOverCell !== day.fullDate,
                  'border-blue-500 border-2 bg-blue-900/30': dragOverCell === day.fullDate && isDragging
                }"
              >
                <!-- Date Number -->
                <div v-if="day.date" class="px-2 py-1 text-right text-xs font-medium flex-shrink-0" :class="day.isToday ? 'text-blue-400 font-bold' : 'text-gray-400'">
                  {{ day.date }}
                </div>
                
                <!-- Events for the day -->
                <div v-if="day.date" class="flex-1 flex flex-col px-1 pb-1">
                  <div 
                    v-for="(event, eIdx) in getEventsForDay(day.fullDate)" 
                    :key="eIdx"
                    @click.stop="openDetail(event, 'calendar')"
                    class="text-[10px] leading-tight truncate cursor-pointer transition-all mb-0.5"
                    :class="[
                      event.isSolid 
                        ? 'text-white px-2 hover:brightness-110 bg-blue-600' 
                        : 'text-gray-200 px-1.5 py-0.5 hover:bg-gray-700 rounded flex items-center gap-1',
                      
                      // 根據是否跨天設置不同的高度
                      event.isSolid && event.isMultiDay ? 'py-0.5' : (event.isSolid ? 'py-1' : ''),
                      
                      // Solid Multi-day Style
                      event.isSolid && !event.isMultiDay ? 'rounded shadow-sm' : '',
                      event.isSolid && event.isMultiDay && event.isStart ? 'rounded-l shadow-sm' : '',
                      event.isSolid && event.isMultiDay && event.isEnd ? 'rounded-r shadow-sm' : '',
                      event.isSolid && event.isMultiDay && !event.isStart && !event.isEnd ? '' : '',
                    ]"
                    :style="getMultiDayStyle(event, idx % 7)"
                    :title="event.summary"
                  >
                    <!-- Solid Event Content -->
                    <span v-if="event.isSolid" class="font-medium">
                      <template v-if="event.isStart || !event.isMultiDay">{{ event.summary }}</template>
                      <template v-else>&nbsp;</template>
                    </span>
                    
                    <!-- Dot Event Content -->
                    <template v-else>
                      <div class="w-1.5 h-1.5 rounded-full bg-blue-400 flex-shrink-0"></div>
                      <span class="text-gray-400 text-[9px] flex-shrink-0 font-medium">{{ event.timeStr }}</span>
                      <span class="truncate">{{ event.summary }}</span>
                    </template>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Detail Modal -->
    <DetailModal 
      v-if="selectedItem" 
      :item="selectedItem" 
      :type="selectedType" 
      @close="closeDetail" 
      @deleted="syncTasks"
    />

    <!-- Add Event Modal -->
    <AddEventModal
      v-if="showAddEventModal && draggedEmail"
      :email="draggedEmail"
      :date="dropTargetDate"
      @close="closeAddEventModal"
      @added="syncTasks"
    />

    <!-- Smart Analysis Modal -->
    <div v-if="showSmartAnalysis" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div class="bg-gray-800 rounded-2xl max-w-6xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
        <div class="sticky top-0 bg-gray-800 border-b border-gray-700 p-4 flex justify-between items-center z-10">
          <h2 class="text-2xl font-bold text-white">🧠 智慧分析</h2>
          <button @click="closeSmartAnalysis" class="text-gray-400 hover:text-white text-2xl">✕</button>
        </div>
        <div class="p-6">
          <SmartAnalysis @close="closeSmartAnalysis" @refreshCalendar="syncTasks" />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: rgba(31, 41, 55, 0.5);
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(75, 85, 99, 0.8);
  border-radius: 3px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(107, 114, 128, 1);
}
</style>
