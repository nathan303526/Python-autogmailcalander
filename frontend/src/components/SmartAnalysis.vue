<template>
  <div class="smart-analysis-container">
    <!-- 分析設定區 -->
    <div v-if="!analysisStarted" class="config-section">
      <div class="header-section mb-8">
        <div class="flex items-center gap-3 mb-2">
          <div class="text-4xl">🧠</div>
          <h2 class="text-3xl font-bold text-white">智慧分析設定</h2>
        </div>
        <p class="text-gray-400 text-sm">使用 AI 自動篩選並分類您的郵件，智慧判斷哪些需要加入日曆</p>
      </div>
      
      <!-- AI 模型卡片 -->
      <div class="card mb-6">
        <div class="card-header">
          <span class="text-lg">🤖</span>
          <h3 class="card-title">AI 模型選擇</h3>
        </div>
        <div class="model-selector">
          <label class="model-option" :class="{ 'selected': modelType === 'gemini' }">
            <input type="radio" v-model="modelType" value="gemini" class="hidden" />
            <div class="model-icon">✨</div>
            <div class="model-info">
              <div class="model-name">Google Gemini</div>
              <div class="model-desc">推薦使用</div>
            </div>
            <div v-if="modelType === 'gemini'" class="check-icon">✓</div>
          </label>
          <label class="model-option" :class="{ 'selected': modelType === 'openai' }">
            <input type="radio" v-model="modelType" value="openai" class="hidden" />
            <div class="model-icon">🔮</div>
            <div class="model-info">
              <div class="model-name">OpenAI GPT</div>
              <div class="model-desc">進階選項</div>
            </div>
            <div v-if="modelType === 'openai'" class="check-icon">✓</div>
          </label>
        </div>
      </div>

      <!-- 意圖選擇卡片 -->
      <div class="card mb-6">
        <div class="card-header">
          <span class="text-lg">🎯</span>
          <h3 class="card-title">分析範圍</h3>
        </div>
        <select v-model="intent" class="select-input">
          <option value="recent">📬 整理最近 N 封信</option>
          <option value="today">📅 整理今天的信</option>
          <option value="unread">✉️ 整理未讀的信</option>
        </select>
        <div v-if="intent === 'recent'" class="mt-4">
          <label class="input-label">
            <span class="label-icon">🔢</span>
            <span>郵件數量</span>
          </label>
          <input 
            v-model.number="emailCount" 
            type="number"
            min="1"
            max="100"
            class="text-input"
            placeholder="輸入要分析的郵件數量 (1-100)"
          />
          <p class="input-hint">⚠️ Gemini API 每分鐘限制 10 個請求，分析 33 封郵件需要約 3-4 分鐘。建議一次分析 10-15 封郵件以獲得最佳體驗。</p>
        </div>
      </div>

      <!-- 關鍵字設定卡片 -->
      <div class="card mb-6">
        <div class="card-header">
          <span class="text-lg">🔍</span>
          <h3 class="card-title">關鍵字篩選</h3>
        </div>
        <div class="space-y-4">
          <div>
            <label class="input-label">
              <span class="label-icon">❌</span>
              <span>移除的關鍵字</span>
            </label>
            <input 
              v-model="removeKeywords" 
              type="text" 
              class="text-input"
            />
            <p class="input-hint">包含這些關鍵字的郵件會被自動過濾，其他郵件都會交由 AI 分析</p>
          </div>
        </div>
      </div>

      <!-- Prompt 設定卡片 -->
      <div class="card mb-6">
        <div class="card-header">
          <span class="text-lg">💬</span>
          <h3 class="card-title">AI 分析指示</h3>
        </div>
        <textarea 
          v-model="customPrompt" 
          rows="4"
          class="textarea-input"
        ></textarea>
        <p class="input-hint mt-2">這段指示會告訴 AI 如何判斷郵件是否需要加入日曆</p>
      </div>

      <!-- API Key 卡片 -->
      <div class="card mb-6">
        <div class="card-header">
          <span class="text-lg">🔑</span>
          <h3 class="card-title">{{ modelType === 'gemini' ? 'Gemini API Key' : 'OpenAI API Key' }}</h3>
        </div>
        <input 
          v-model="apiKey" 
          type="password" 
          :placeholder="modelType === 'gemini' ? '輸入您的 Gemini API Key (AIza...)' : '輸入您的 OpenAI API Key (sk-...)'"
          class="text-input"
        />
        <a 
          :href="modelType === 'gemini' ? 'https://aistudio.google.com/app/apikey' : 'https://platform.openai.com/api-keys'"
          target="_blank"
          class="api-link"
        >
          🔗 {{ modelType === 'gemini' ? '取得 Gemini API Key' : '取得 OpenAI API Key' }}
        </a>
        <p class="input-hint mt-2">💾 Token 存於 SessionStorage (關閉分頁即清除)</p>
      </div>

      <!-- 開始分析按鈕 -->
      <button 
        @click="startAnalysis" 
        :disabled="analyzing"
        class="analyze-button"
      >
        <span v-if="analyzing" class="animate-spin">⏳</span>
        <span v-else>🚀</span>
        <span>{{ analyzing ? '正在分析中...' : '開始智慧分析' }}</span>
      </button>
    </div>

    <!-- 分析結果預覽區 -->
    <div v-else class="preview-section">
      <div class="header-section mb-6">
        <div class="flex items-center gap-3 mb-2">
          <div class="text-3xl">📊</div>
          <h2 class="text-3xl font-bold text-white">分析結果預覽</h2>
        </div>
        <div class="flex gap-6 text-sm">
          <button 
            @click="currentTab = 'matched'"
            class="stat-badge" 
            :class="currentTab === 'matched' ? 'stat-success-active' : 'stat-success'"
          >
            ✅ 將加入: {{ matchedPairs.length }} 封
          </button>
          <button 
            @click="currentTab = 'removed'"
            class="stat-badge" 
            :class="currentTab === 'removed' ? 'stat-danger-active' : 'stat-danger'"
          >
            ❌ 已移除: {{ removedEmails.length }} 封
          </button>
          <button 
            @click="currentTab = 'pending'"
            class="stat-badge" 
            :class="currentTab === 'pending' ? 'stat-pending-active' : 'stat-pending'"
          >
            ⏳ 待定: {{ pendingEmails.length }} 封
          </button>
        </div>
      </div>

      <!-- AI 整理重點 -->
      <div v-if="analysisSummary" class="summary-card mb-6">
        <div class="summary-header">
          <span class="text-2xl">🧠</span>
          <h3 class="summary-title">AI 整理重點</h3>
        </div>
        <div class="summary-content" v-html="analysisSummary"></div>
      </div>

      <!-- 左右分欄布局 -->
      <div class="preview-grid">
        <!-- 左側：郵件列表 -->
        <div class="emails-panel">
          <h3 class="panel-title">📧 郵件列表</h3>
          
          <!-- 將加入的郵件 -->
          <div v-if="currentTab === 'matched'" class="emails-scroll">
            <div v-if="matchedPairs.length === 0" class="empty-state">
              <div class="text-4xl mb-2">📭</div>
              <div class="text-gray-500">沒有符合的郵件</div>
            </div>
            <div 
              v-for="pair in matchedPairs" 
              :key="pair.email.id"
              class="email-card"
              :style="{ borderLeft: `4px solid ${pair.color}` }"
              @mouseenter="hoveredEmailId = pair.email.id"
              @mouseleave="hoveredEmailId = null"
            >
              <div class="flex items-start gap-3">
                <div class="color-indicator" :style="{ backgroundColor: pair.color }"></div>
                <div class="flex-1">
                  <div class="email-subject">{{ pair.email.subject }}</div>
                  <div class="email-snippet">{{ pair.email.snippet }}</div>
                  <div class="email-meta">
                    <span class="meta-item">📅 {{ pair.suggestedDate }}</span>
                    <span class="meta-item">⏰ {{ pair.suggestedTime }}</span>
                    <span class="meta-item">💯 {{ (pair.confidence * 100).toFixed(0) }}%</span>
                  </div>
                  <div class="ai-reason">
                    <span class="reason-label">🤖 AI 分析：</span>
                    <span class="reason-text">{{ pair.source }}</span>
                  </div>
                  <!-- 可編輯日期 -->
                  <div class="date-edit">
                    <input 
                      v-model="pair.suggestedDate" 
                      type="date"
                      class="date-input"
                    />
                    <input 
                      v-model="pair.suggestedTime" 
                      type="time"
                      class="time-input"
                    />
                  </div>
                </div>
                <button 
                  @click="removePair(pair.email.id)"
                  class="remove-btn"
                  title="移除此配對"
                >
                  ✕
                </button>
              </div>
            </div>
          </div>

          <!-- 已移除的郵件 -->
          <div v-else-if="currentTab === 'removed'" class="emails-scroll">
            <div v-if="removedEmails.length === 0" class="empty-state">
              <div class="text-4xl mb-2">✅</div>
              <div class="text-gray-500">沒有被移除的郵件</div>
            </div>
            <div 
              v-for="email in removedEmails" 
              :key="email.id"
              class="email-card removed-card"
            >
              <div class="flex items-start gap-3">
                <div class="flex-1">
                  <div class="email-subject">❌ {{ email.subject }}</div>
                  <div class="email-snippet">{{ email.snippet }}</div>
                  <div class="ai-reason removed-reason">
                    <span class="reason-label">🚫 移除原因：</span>
                    <span class="reason-text">{{ email.removeReason || '包含移除關鍵字' }}</span>
                  </div>
                  <div v-if="email.confidence !== undefined" class="ai-confidence">
                    <span class="confidence-label">AI 信心指數：</span>
                    <span class="confidence-value">{{ (email.confidence * 100).toFixed(0) }}%</span>
                  </div>
                </div>
                <button 
                  @click="addRemovedToMatched(email)"
                  class="add-btn"
                  title="重新加入到將加入列表"
                >
                  ✓
                </button>
              </div>
            </div>
          </div>

          <!-- 未定的郵件 -->
          <div v-else-if="currentTab === 'pending'" class="emails-scroll">
            <div v-if="pendingEmails.length === 0" class="empty-state">
              <div class="text-4xl mb-2">🎉</div>
              <div class="text-gray-500">沒有時間衝突的郵件</div>
            </div>
              <div 
                v-for="pair in pendingEmails" 
                :key="pair.email.id"
                class="email-card pending-card"
              >
                <div class="flex items-start gap-3">
                  <div class="flex-1">
                    <div class="email-subject">⏳ {{ pair.email.subject }}</div>
                    <div class="email-snippet">{{ pair.email.snippet }}</div>
                    <div class="ai-reason pending-reason">
                      <span class="reason-label">⚠️ 時間衝突：</span>
                      <span class="reason-text">該日期已有 {{ pair.conflictEvents.length }} 個事件</span>
                    </div>
                    <div class="conflict-list">
                      <div v-for="(evt, idx) in pair.conflictEvents" :key="idx" class="conflict-item">
                        📅 {{ evt.summary }} - {{ formatDateTime(evt.start) }}
                      </div>
                    </div>
                    <!-- 修改時間 -->
                    <div class="date-edit">
                      <label class="edit-label">修改為：</label>
                      <input 
                        v-model="pair.suggestedDate" 
                        type="date"
                        class="date-input"
                      />
                      <input 
                        v-model="pair.suggestedTime" 
                        type="time"
                        class="time-input"
                      />
                    </div>
                  </div>
                  <button 
                    @click="addPendingToMatched(pair)"
                    class="add-btn"
                    title="確認修改並加入"
                  >
                    ✓
                  </button>
                </div>
              </div>
          </div>
        </div>

        <!-- 右側：日曆預覽 -->
        <div class="calendar-panel">
          <h3 class="panel-title">📅 日曆預覽</h3>
          <div class="mini-calendar">
            <div class="calendar-header">
              <button @click="changePreviewMonth(-1)" class="month-nav">◀</button>
              <div class="current-month">{{ previewYear }}年 {{ previewMonth + 1 }}月</div>
              <button @click="changePreviewMonth(1)" class="month-nav">▶</button>
            </div>
            
            <!-- 星期標題 -->
            <div class="weekdays">
              <div v-for="day in ['日', '一', '二', '三', '四', '五', '六']" :key="day" class="weekday">
                {{ day }}
              </div>
            </div>
            
            <!-- 日期網格 -->
            <div class="dates-grid">
              <div 
                v-for="day in calendarDays" 
                :key="day.fullDate"
                class="date-cell"
                :class="{
                  'empty': !day.date,
                  'today': day.isToday,
                  'has-event': day.events.length > 0
                }"
              >
                <div class="date-number">{{ day.date }}</div>
                <div v-if="day.events.length > 0" class="event-indicators">
                  <div 
                    v-for="event in day.events" 
                    :key="event.email.id"
                    class="event-dot"
                    :class="{ 'event-dot-hovered': hoveredEmailId === event.email.id }"
                    :style="{ backgroundColor: event.color }"
                    :title="event.email.subject"
                  >
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 操作按鈕 -->
      <div class="action-buttons">
        <button 
          @click="resetAnalysis"
          class="btn-secondary"
        >
          ↩️ 重新設定
        </button>
        <button 
          @click="confirmAddToCalendar" 
          :disabled="matchedPairs.length === 0 || adding"
          class="btn-primary"
        >
          <span v-if="adding" class="animate-spin">⏳</span>
          <span v-else>✅</span>
          <span>{{ adding ? '加入中...' : `確認加入 ${matchedPairs.length} 個行程` }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import axios from 'axios'
import { API_BASE } from '../config'

const emit = defineEmits(['close', 'refreshCalendar'])

// 設定狀態
const intent = ref('recent')
const emailCount = ref(20)
const removeKeywords = ref('廣告, 促銷, 垃圾郵件, 中大短程接駁車, 衛生保健組')
const customPrompt = ref('如果你是一位機械系的大學生，請分析這封郵件是否包含需要加入到行事曆裡面。如果是，請返回建議的日期和時間。')
const apiKey = ref('')
const modelType = ref('gemini') // 'openai' or 'gemini'

// 從 SessionStorage 載入 API Keys
onMounted(() => {
  const storedOpenAI = sessionStorage.getItem('smart_analysis_openai_key')
  const storedGemini = sessionStorage.getItem('smart_analysis_gemini_key')
  
  if (modelType.value === 'openai' && storedOpenAI) {
    apiKey.value = storedOpenAI
  } else if (modelType.value === 'gemini' && storedGemini) {
    apiKey.value = storedGemini
  }
})

// 監聽 API Key 變化並存入 SessionStorage
watch(apiKey, (newVal) => {
  if (newVal) {
    if (modelType.value === 'gemini') {
      sessionStorage.setItem('smart_analysis_gemini_key', newVal)
    } else if (modelType.value === 'openai') {
      sessionStorage.setItem('smart_analysis_openai_key', newVal)
    }
  }
})

// 監聽模型切換，載入對應的 API Key
watch(modelType, (newType) => {
  if (newType === 'gemini') {
    const stored = sessionStorage.getItem('smart_analysis_gemini_key')
    apiKey.value = stored || ''
  } else if (newType === 'openai') {
    const stored = sessionStorage.getItem('smart_analysis_openai_key')
    apiKey.value = stored || ''
  }
})


// 分析狀態
const analysisStarted = ref(false)
const analyzing = ref(false)
const adding = ref(false)
const currentTab = ref('matched') // 'matched', 'removed', 'pending'
const hoveredEmailId = ref(null) // 追蹤正在hover的郵件

// 結果
const matchedPairs = ref([])
const removedEmails = ref([])
const pendingEmails = ref([])
const analysisSummary = ref('')

// 日曆預覽狀態
const previewYear = ref(new Date().getFullYear())
const previewMonth = ref(new Date().getMonth())

// 計算日曆網格
const calendarDays = computed(() => {
  const year = previewYear.value
  const month = previewMonth.value
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  const daysInMonth = lastDay.getDate()
  const startDayOfWeek = firstDay.getDay()
  
  const days = []
  const today = new Date()
  
  // 前面的空白
  for (let i = 0; i < startDayOfWeek; i++) {
    days.push({ date: null, fullDate: null, isToday: false, events: [] })
  }
  
  // 當月日期
  for (let i = 1; i <= daysInMonth; i++) {
    const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(i).padStart(2, '0')}`
    const isToday = today.getFullYear() === year && today.getMonth() === month && today.getDate() === i
    
    // 找到該日期的所有郵件
    const events = matchedPairs.value.filter(pair => pair.suggestedDate === dateStr)
    
    days.push({
      date: i,
      fullDate: dateStr,
      isToday,
      events
    })
  }
  
  return days
})

const changePreviewMonth = (delta) => {
  const newMonth = previewMonth.value + delta
  if (newMonth < 0) {
    previewMonth.value = 11
    previewYear.value--
  } else if (newMonth > 11) {
    previewMonth.value = 0
    previewYear.value++
  } else {
    previewMonth.value = newMonth
  }
}

// 顏色池
const colors = [
  '#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6',
  '#EC4899', '#14B8A6', '#F97316', '#6366F1', '#84CC16'
]

let colorIndex = 0
const getNextColor = () => {
  // 取得目前已使用的顏色
  const usedColors = matchedPairs.value.map(p => p.color)
  
  // 如果還有未使用的顏色，優先使用
  const availableColors = colors.filter(c => !usedColors.includes(c))
  if (availableColors.length > 0) {
    return availableColors[0]
  }
  
  // 如果所有顏色都用完了，循環使用
  const color = colors[colorIndex % colors.length]
  colorIndex++
  return color
}

const startAnalysis = async () => {
  // 檢查是否已完成 Google 授權
  const syncedData = localStorage.getItem('synced_tasks')
  if (!syncedData) {
    alert('❌ 尚未完成 Google 授權！\n\n請先關閉此視窗，在主頁面點擊「同步 Gmail & Calendar」按鈕完成 Google 帳號連結，然後再使用智慧分析功能。')
    return
  }

  if (!apiKey.value.trim()) {
    alert(`請輸入 ${modelType.value === 'gemini' ? 'Gemini' : 'OpenAI'} API Key`)
    return
  }

  analyzing.value = true
  
  try {
    const response = await axios.post(`${API_BASE}/smart-analysis`, {
      intent: intent.value,
      email_count: intent.value === 'recent' ? emailCount.value : null,
      add_keywords: [],  // 不使用關鍵字匹配，全部交給 AI
      remove_keywords: removeKeywords.value.split(',').map(k => k.trim()).filter(k => k),
      custom_prompt: customPrompt.value,
      api_key: apiKey.value,
      model_type: modelType.value
    })

    // 處理結果
    matchedPairs.value = response.data.matched.map(item => ({
      ...item,
      // 確保日期時間不是 null 字符串
      suggestedDate: item.suggestedDate && item.suggestedDate !== 'null' ? item.suggestedDate : new Date().toISOString().split('T')[0],
      suggestedTime: item.suggestedTime && item.suggestedTime !== 'null' ? item.suggestedTime : '09:00',
      color: getNextColor()
    }))
    removedEmails.value = response.data.removed
    pendingEmails.value = response.data.pending
    
    // 處理摘要
    if (response.data.summary) {
      analysisSummary.value = response.data.summary.replace(/\n/g, '<br>')
    }

    analysisStarted.value = true
  } catch (error) {
    console.error('分析失敗:', error)
    console.error('錯誤詳情:', error.response)
    
    if (error.response?.status === 401) {
      const detail = error.response?.data?.detail || 'Unauthorized'
      alert(`❌ Google 授權已過期或失效！\n\n錯誤詳情: ${detail}\n\n解決方法:\n1. 關閉此視窗\n2. 在主頁面點擊「同步 Gmail & Calendar」\n3. 重新連結 Google 帳號\n4. 完成後再使用智慧分析功能`)
    } else if (error.response?.status === 400) {
      alert('❌ 請求格式錯誤:\n' + (error.response?.data?.detail || error.message))
    } else if (error.response?.status === 500) {
      alert('❌ 伺服器錯誤:\n' + (error.response?.data?.detail || error.message) + '\n\n請檢查後端日誌以獲取更多信息')
    } else {
      alert('❌ 分析失敗:\n' + (error.response?.data?.detail || error.message))
    }
  } finally {
    analyzing.value = false
  }
}

const removePair = (emailId) => {
  const index = matchedPairs.value.findIndex(p => p.email.id === emailId)
  if (index !== -1) {
    matchedPairs.value.splice(index, 1)
  }
}

const confirmAddToCalendar = async () => {
  adding.value = true
  
  try {
    const events = matchedPairs.value.map(pair => {
      // 確保所有必需字段都存在
      const email = pair.email || {}
      const snippet = email.snippet || ''
      
      // 簡化描述，只保留郵件重點（前200字）
      const description = snippet.length > 200 
        ? snippet.substring(0, 200) + '...'
        : snippet
      
      // 如果沒有時間，設為全天事件
      const isAllDay = !pair.suggestedTime || pair.suggestedTime === ''
      
      return {
        title: email.subject || '未命名事件',
        date: pair.suggestedDate || new Date().toISOString().split('T')[0],
        time: isAllDay ? null : pair.suggestedTime,
        isAllDay: isAllDay,
        description: description
      }
    })


    // 批量加入
    await axios.post(`${API_BASE}/calendar/batch-add-events`, {
      events: events
    })

    alert('成功加入 ' + events.length + ' 個行程！')
    emit('refreshCalendar')
    emit('close')
  } catch (error) {
    console.error('加入行程失敗:', error)
    console.error('錯誤詳情:', error.response?.data)
    alert('加入失敗: ' + (error.response?.data?.detail || error.message))
  } finally {
    adding.value = false
  }
}

const resetAnalysis = () => {
  analysisStarted.value = false
  matchedPairs.value = []
  removedEmails.value = []
  pendingEmails.value = []
  analysisSummary.value = ''
  colorIndex = 0
}

const addPendingToMatched = (pair) => {
  // 從待定列表中移除
  const index = pendingEmails.value.findIndex(p => p.email.id === pair.email.id)
  if (index !== -1) {
    pendingEmails.value.splice(index, 1)
  }
  
  // 加入到將加入列表（使用修改後的時間）
  matchedPairs.value.push({
    email: pair.email,
    suggestedDate: pair.suggestedDate,
    suggestedTime: pair.suggestedTime,
    confidence: pair.confidence || 0.8,
    source: pair.source || '手動調整時間',
    color: getNextColor()
  })
  
  // 切換到將加入分頁
  currentTab.value = 'matched'
}

const addRemovedToMatched = (email) => {
  // 從已移除列表中移除
  const index = removedEmails.value.findIndex(e => e.id === email.id)
  if (index !== -1) {
    removedEmails.value.splice(index, 1)
  }
  
  // 加入到將加入列表
  const tomorrow = new Date()
  tomorrow.setDate(tomorrow.getDate() + 1)
  const suggestedDate = tomorrow.toISOString().split('T')[0]
  
  matchedPairs.value.push({
    email: {
      id: email.id,
      subject: email.subject,
      snippet: email.snippet,
      date: email.date
    },
    suggestedDate: suggestedDate,
    suggestedTime: '09:00',
    confidence: 0.5,
    source: '手動重新加入',
    color: getNextColor()
  })
  
  // 切換到將加入分頁
  currentTab.value = 'matched'
}

const formatDateTime = (dateTimeStr) => {
  try {
    const date = new Date(dateTimeStr)
    return date.toLocaleString('zh-TW', {
      month: 'numeric',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return dateTimeStr
  }
}
</script>

<style scoped>
.smart-analysis-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
}

/* 狀態徽章 */
.stat-badge {
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.stat-success {
  background: rgba(16, 185, 129, 0.2);
  color: rgb(16, 185, 129);
}

.stat-success-active {
  background: rgba(16, 185, 129, 0.4);
  color: rgb(16, 185, 129);
  border-color: rgb(16, 185, 129);
}

.stat-danger {
  background: rgba(239, 68, 68, 0.2);
  color: rgb(239, 68, 68);
}

.stat-danger-active {
  background: rgba(239, 68, 68, 0.4);
  color: rgb(239, 68, 68);
  border-color: rgb(239, 68, 68);
}

.stat-pending {
  background: rgba(245, 158, 11, 0.2);
  color: rgb(245, 158, 11);
}

.stat-pending-active {
  background: rgba(245, 158, 11, 0.4);
  color: rgb(245, 158, 11);
  border-color: rgb(245, 158, 11);
}

/* AI 摘要卡片 */
.summary-card {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(139, 92, 246, 0.15));
  border: 2px solid rgba(96, 165, 250, 0.4);
  border-radius: 16px;
  padding: 1.5rem;
  backdrop-filter: blur(10px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
}

.summary-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 2px solid rgba(96, 165, 250, 0.3);
}

.summary-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: white;
}

.summary-content {
  color: rgb(191, 219, 254);
  font-size: 0.95rem;
  line-height: 1.8;
  white-space: pre-wrap;
}

.summary-content::v-deep strong {
  color: rgb(147, 197, 253);
  font-weight: 600;
}

.summary-content::v-deep ul {
  margin: 0.5rem 0;
  padding-left: 1.5rem;
}

.summary-content::v-deep li {
  margin: 0.25rem 0;
}

/* 左右分欄布局 */
.preview-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  margin-bottom: 2rem;
  height: 600px;
  max-height: 600px;
  overflow: hidden;
}

/* 面板樣式 */
.emails-panel,
.calendar-panel {
  background: rgba(55, 65, 81, 0.5);
  border: 1px solid rgba(75, 85, 99, 0.6);
  border-radius: 16px;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 100%;
  max-height: 600px;
}

.panel-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: white;
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 2px solid rgba(75, 85, 99, 0.6);
}

/* 郵件列表 */
.emails-scroll {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 0.5rem;
  max-height: 100%;
  min-height: 0;
}

.emails-scroll::-webkit-scrollbar {
  width: 6px;
}

.emails-scroll::-webkit-scrollbar-track {
  background: rgba(31, 41, 55, 0.3);
  border-radius: 3px;
}

.emails-scroll::-webkit-scrollbar-thumb {
  background: rgba(96, 165, 250, 0.5);
  border-radius: 3px;
}

.emails-scroll::-webkit-scrollbar-thumb:hover {
  background: rgba(96, 165, 250, 0.7);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  flex-shrink: 0;
}

.email-card {
  background: rgba(31, 41, 55, 0.6);
  border-radius: 12px;
  padding: 1rem;
  margin-bottom: 0.75rem;
  transition: all 0.3s;
}

.email-card:hover {
  background: rgba(31, 41, 55, 0.9);
  transform: translateX(4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.removed-card {
  border-left: 4px solid rgb(239, 68, 68) !important;
  opacity: 0.7;
}

.pending-card {
  border-left: 4px solid rgb(245, 158, 11) !important;
  opacity: 0.8;
}

.color-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 0.25rem;
}

.email-subject {
  font-weight: 600;
  color: white;
  font-size: 0.95rem;
  margin-bottom: 0.5rem;
}

.email-snippet {
  font-size: 0.85rem;
  color: rgb(156, 163, 175);
  margin-bottom: 0.75rem;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.email-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.meta-item {
  font-size: 0.75rem;
  color: rgb(156, 163, 175);
}

.ai-reason {
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 8px;
  padding: 0.5rem;
  margin-bottom: 0.75rem;
  font-size: 0.8rem;
}

.reason-label {
  color: rgb(96, 165, 250);
  font-weight: 600;
}

.reason-text {
  color: rgb(191, 219, 254);
}

.removed-reason {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.3);
}

.removed-reason .reason-label {
  color: rgb(248, 113, 113);
}

.removed-reason .reason-text {
  color: rgb(254, 202, 202);
}

.pending-reason {
  background: rgba(245, 158, 11, 0.1);
  border-color: rgba(245, 158, 11, 0.3);
}

.pending-reason .reason-label {
  color: rgb(251, 191, 36);
}

.pending-reason .reason-text {
  color: rgb(253, 230, 138);
}

.ai-confidence {
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: rgba(96, 165, 250, 0.1);
  border-left: 3px solid rgba(96, 165, 250, 0.5);
  border-radius: 4px;
  font-size: 0.85rem;
}

.confidence-label {
  color: rgb(147, 197, 253);
  font-weight: 500;
}

.confidence-value {
  color: rgb(191, 219, 254);
  font-weight: 600;
}

.conflict-list {
  margin-top: 0.75rem;
  padding: 0.75rem;
  background: rgba(245, 158, 11, 0.05);
  border: 1px solid rgba(245, 158, 11, 0.2);
  border-radius: 6px;
}

.conflict-item {
  padding: 0.5rem;
  margin-bottom: 0.5rem;
  background: rgba(17, 24, 39, 0.4);
  border-radius: 4px;
  color: rgb(253, 230, 138);
  font-size: 0.85rem;
}

.conflict-item:last-child {
  margin-bottom: 0;
}

.edit-label {
  display: block;
  margin-bottom: 0.5rem;
  color: rgb(156, 163, 175);
  font-size: 0.85rem;
  font-weight: 500;
}

.date-edit {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.75rem;
}

.date-input,
.time-input {
  flex: 1;
  padding: 0.5rem;
  background: rgba(17, 24, 39, 0.6);
  border: 1px solid rgba(75, 85, 99, 0.6);
  border-radius: 6px;
  color: white;
  font-size: 0.85rem;
}

.remove-btn {
  color: rgb(239, 68, 68);
  font-size: 1.25rem;
  font-weight: bold;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  border-radius: 6px;
  transition: all 0.2s;
}

.remove-btn:hover {
  background: rgba(239, 68, 68, 0.2);
}

.add-btn {
  color: rgb(16, 185, 129);
  font-size: 1.5rem;
  font-weight: bold;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  border-radius: 6px;
  transition: all 0.2s;
}

.add-btn:hover {
  background: rgba(16, 185, 129, 0.2);
  transform: scale(1.1);
}

/* 日曆預覽 */
.mini-calendar {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.calendar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.month-nav {
  background: rgba(75, 85, 99, 0.6);
  border: none;
  color: white;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.month-nav:hover {
  background: rgba(96, 165, 250, 0.6);
}

.current-month {
  font-weight: 600;
  color: white;
  font-size: 1.1rem;
}

.weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
  margin-bottom: 4px;
}

.weekday {
  text-align: center;
  font-size: 0.75rem;
  color: rgb(156, 163, 175);
  font-weight: 600;
  padding: 0.5rem 0;
}

.dates-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  grid-auto-rows: minmax(70px, auto);
  gap: 4px;
}

.date-cell {
  background: rgba(31, 41, 55, 0.4);
  border-radius: 8px;
  padding: 0.5rem;
  display: flex;
  flex-direction: column;
  transition: all 0.2s;
  position: relative;
}

.date-cell.empty {
  background: transparent;
}

.date-cell.today {
  background: rgba(59, 130, 246, 0.2);
  border: 2px solid rgb(59, 130, 246);
}

.date-cell.has-event {
  background: rgba(31, 41, 55, 0.8);
}

.date-number {
  font-size: 0.85rem;
  color: white;
  font-weight: 500;
  margin-bottom: 0.25rem;
}

.event-indicators {
  width: 100%;
  display: flex;
  flex-wrap: wrap;
  gap: 3px;
  margin-top: 4px;
  justify-content: center;
}

.event-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

.event-dot:hover {
  transform: scale(1.5);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
}

.event-dot-hovered {
  transform: scale(2) !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.7) !important;
  z-index: 10;
  animation: pulse 0.5s ease-in-out;
}

@keyframes pulse {
  0%, 100% { transform: scale(2); }
  50% { transform: scale(2.2); }
}

/* 操作按鈕 */
.action-buttons {
  display: flex;
  gap: 1rem;
}

.btn-primary,
.btn-secondary {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 1rem;
  font-size: 1rem;
  font-weight: 600;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-primary {
  background: linear-gradient(135deg, rgb(16, 185, 129), rgb(5, 150, 105));
  color: white;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
}

.btn-primary:hover:not(:disabled) {
  background: linear-gradient(135deg, rgb(5, 150, 105), rgb(4, 120, 87));
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.6);
  transform: translateY(-2px);
}

.btn-primary:disabled {
  background: rgb(75, 85, 99);
  cursor: not-allowed;
  box-shadow: none;
}

.btn-secondary {
  background: rgba(75, 85, 99, 0.6);
  color: white;
}

.btn-secondary:hover {
  background: rgba(75, 85, 99, 0.9);
}

/* 卡片樣式 */
.card {
  background: rgba(55, 65, 81, 0.5);
  border: 1px solid rgba(75, 85, 99, 0.6);
  border-radius: 16px;
  padding: 1.5rem;
  backdrop-filter: blur(10px);
  transition: all 0.3s;
}

.card:hover {
  background: rgba(55, 65, 81, 0.7);
  border-color: rgba(96, 165, 250, 0.5);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.card-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: white;
}

/* 模型選擇器 */
.model-selector {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.model-option {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: rgba(31, 41, 55, 0.5);
  border: 2px solid rgba(75, 85, 99, 0.6);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s;
}

.model-option:hover {
  background: rgba(31, 41, 55, 0.8);
  border-color: rgba(96, 165, 250, 0.6);
  transform: translateY(-2px);
}

.model-option.selected {
  background: rgba(59, 130, 246, 0.2);
  border-color: rgb(59, 130, 246);
  box-shadow: 0 0 20px rgba(59, 130, 246, 0.3);
}

.model-icon {
  font-size: 2rem;
  line-height: 1;
}

.model-info {
  flex: 1;
}

.model-name {
  font-weight: 600;
  color: white;
  font-size: 1rem;
}

.model-desc {
  font-size: 0.75rem;
  color: rgb(156, 163, 175);
  margin-top: 0.25rem;
}

.check-icon {
  color: rgb(59, 130, 246);
  font-size: 1.5rem;
  font-weight: bold;
}

/* 輸入框樣式 */
.select-input {
  width: 100%;
  padding: 0.875rem 1rem;
  background: rgba(31, 41, 55, 0.6);
  border: 1px solid rgba(75, 85, 99, 0.6);
  border-radius: 10px;
  color: white;
  font-size: 1rem;
  outline: none;
  transition: all 0.3s;
}

.select-input:focus {
  border-color: rgb(59, 130, 246);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.input-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: rgb(229, 231, 235);
  margin-bottom: 0.5rem;
}

.label-icon {
  font-size: 1rem;
}

.text-input {
  width: 100%;
  padding: 0.875rem 1rem;
  background: rgba(31, 41, 55, 0.6);
  border: 1px solid rgba(75, 85, 99, 0.6);
  border-radius: 10px;
  color: white;
  font-size: 0.95rem;
  outline: none;
  transition: all 0.3s;
}

.text-input:focus {
  border-color: rgb(59, 130, 246);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  background: rgba(31, 41, 55, 0.8);
}

.textarea-input {
  width: 100%;
  padding: 0.875rem 1rem;
  background: rgba(31, 41, 55, 0.6);
  border: 1px solid rgba(75, 85, 99, 0.6);
  border-radius: 10px;
  color: white;
  font-size: 0.95rem;
  outline: none;
  resize: vertical;
  transition: all 0.3s;
  font-family: inherit;
}

.textarea-input:focus {
  border-color: rgb(59, 130, 246);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  background: rgba(31, 41, 55, 0.8);
}

.input-hint {
  font-size: 0.75rem;
  color: rgb(156, 163, 175);
  margin-top: 0.5rem;
}

.api-link {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.75rem;
  font-size: 0.875rem;
  color: rgb(96, 165, 250);
  text-decoration: none;
  transition: color 0.2s;
}

.api-link:hover {
  color: rgb(147, 197, 253);
  text-decoration: underline;
}

/* 按鈕樣式 */
.analyze-button {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 1rem;
  background: linear-gradient(135deg, rgb(59, 130, 246), rgb(37, 99, 235));
  color: white;
  font-size: 1.125rem;
  font-weight: 600;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

.analyze-button:hover:not(:disabled) {
  background: linear-gradient(135deg, rgb(37, 99, 235), rgb(29, 78, 216));
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.6);
  transform: translateY(-2px);
}

.analyze-button:disabled {
  background: rgb(75, 85, 99);
  cursor: not-allowed;
  box-shadow: none;
}


</style>
