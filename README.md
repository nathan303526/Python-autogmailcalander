# 📧 智慧郵件管理系統 (Smart Email & Calendar Manager)

一個結合 AI 智慧分析的郵件與行事曆管理系統，使用 Google Gmail API、Google Calendar API 以及 Gemini/OpenAI AI 模型，自動分析郵件內容並智慧地加入到 Google Calendar 中。

## 🎯 專案特色

### 核心功能
- **🔐 Google OAuth 2.0 整合**：安全的 Gmail 和 Calendar 授權連結
- **🧠 AI 智慧郵件分析**：使用 Gemini 或 OpenAI 自動判斷郵件是否需要加入行事曆
- **📅 自動日曆管理**：智慧提取郵件中的日期、時間資訊並加入 Calendar
- **🎨 視覺化預覽**：分割視圖顯示郵件列表與日曆預覽，並使用顏色區分不同事件
- **⚡ 批次處理**：支援一次分析多封郵件，並自動處理 API 速率限制
- **🔄 衝突檢測**：自動檢測日曆時間衝突並提供調整選項

### 輔助功能
- **🌤️ 天氣查詢**：顯示當前位置天氣資訊
- **🍽️ 餐廳推薦**：隨機推薦附近餐廳
- **💬 多模組 AI 對話**：支援 Gemini 和 OpenAI 多模型對話

## 🛠️ 技術架構

### 後端 (Backend)
- **框架**: FastAPI (Python 3.11)
- **AI 模型**: Google Gemini API, OpenAI GPT API
- **Google API**: Gmail API (v1), Google Calendar API (v3)
- **認證**: OAuth 2.0 with token refresh
- **部署**: Docker + Uvicorn

### 前端 (Frontend)
- **框架**: Vue 3 (Composition API)
- **UI**: Tailwind CSS
- **HTTP 客戶端**: Axios
- **建置工具**: Vite
- **部署**: Docker + Nginx

### DevOps
- **容器化**: Docker Compose
- **CI/CD**: Multi-stage Docker builds
- **環境管理**: 環境變數與 SessionStorage

## 📦 專案結構

```
期末專題/
├── backend/                 # FastAPI 後端
│   ├── main.py             # 主程式 (API 路由)
│   ├── Oauth.py            # Google OAuth 處理
│   ├── data.py             # 餐廳資料庫
│   ├── requirements.txt    # Python 依賴套件
│   ├── Dockerfile          # 後端容器配置
│   ├── credentials.json    # Google OAuth 憑證 (需自行取得)
│   └── token.json          # OAuth Token (自動生成)
│
├── frontend/               # Vue 3 前端
│   ├── src/
│   │   ├── components/     # Vue 組件
│   │   │   ├── SmartAnalysis.vue    # 智慧分析主組件
│   │   │   ├── MultiAI.vue          # 多模組 AI 對話
│   │   │   └── ...
│   │   ├── App.vue         # 根組件
│   │   └── main.js         # 入口文件
│   ├── package.json        # Node.js 依賴
│   ├── vite.config.js      # Vite 配置
│   └── Dockerfile          # 前端容器配置
│
├── docker-compose.yml      # Docker Compose 配置
└── README.md               # 專案說明文件
```

## 🚀 快速開始

### 前置需求

1. **Docker & Docker Compose** (推薦)
   - Docker Desktop 4.0+
   - Docker Compose v2.0+

2. **或本地開發環境**
   - Python 3.11+
   - Node.js 18+
   - npm 或 yarn

3. **Google API 憑證**
   - 前往 [Google Cloud Console](https://console.cloud.google.com/)
   - 建立新專案並啟用 Gmail API 和 Google Calendar API
   - 建立 OAuth 2.0 憑證 (桌面應用程式)
   - 下載 `credentials.json` 並放入 `backend/` 資料夾

4. **AI API Keys**
   - Gemini API Key: [Google AI Studio](https://aistudio.google.com/app/apikey)
   - OpenAI API Key: [OpenAI Platform](https://platform.openai.com/api-keys)

### 方法一：Docker 部署 (推薦)

```bash
# 1. 克隆專案
git clone <repository-url>
cd 期末專題

# 2. 確保 credentials.json 已放入 backend/

# 3. 啟動容器
docker-compose up -d

# 4. 查看日誌
docker-compose logs -f

# 5. 停止容器
docker-compose down
```

服務將會啟動於：
- 前端: http://localhost:5173
- 後端: http://localhost:8000
- API 文件: http://localhost:8000/docs

### 方法二：本地開發

#### 後端設定

```bash
cd backend

# 建立虛擬環境
python -m venv .venv

# 啟動虛擬環境 (Windows)
.venv\Scripts\Activate
# 啟動虛擬環境 (Mac/Linux)
# source .venv/bin/activate

# 安裝依賴
pip install -r requirements.txt

# 啟動後端伺服器
python main.py
```

#### 前端設定

```bash
cd frontend

# 安裝依賴
npm install

# 啟動開發伺服器
npm run dev
```

## 📖 使用指南

### 1. Google 授權連結

1. 打開首頁 http://localhost:5173
2. 點擊「**同步 Gmail & Calendar**」按鈕
3. 在彈出的瀏覽器視窗中登入 Google 帳號
4. 授權應用程式存取 Gmail 和 Calendar
5. 授權成功後，資料會顯示在頁面上

### 2. 智慧郵件分析

1. 點擊「**🧠 智慧分析**」按鈕
2. 選擇 AI 模型 (Gemini 推薦 / OpenAI 進階)
3. 設定分析範圍：
   - **最近 N 封信**：自訂數量 (1-100)
   - **今天的信**：僅分析今日收到的郵件
   - **未讀的信**：僅分析未讀郵件
4. 設定移除關鍵字 (例如：廣告、促銷、垃圾郵件)
5. 輸入 AI 分析指示 (Prompt)
6. 輸入對應的 API Key (會自動保存到 SessionStorage)
7. 點擊「**開始智慧分析**」

### 3. 查看分析結果

分析完成後會顯示三個分類：

- **✅ 將加入** (綠色)：AI 判斷需要加入行事曆的郵件
  - 可編輯日期和時間
  - 可移除不需要的項目
  - 右側日曆會顯示顏色點標記
  
- **❌ 已移除** (紅色)：包含移除關鍵字或 AI 判斷不需要的郵件
  - 顯示移除原因
  - 可重新加入到「將加入」列表
  
- **⏳ 待定** (黃色)：時間有衝突的郵件
  - 顯示衝突的事件
  - 可修改時間後加入

### 4. 確認加入行事曆

1. 檢查「將加入」列表中的郵件
2. 確認或調整日期、時間
3. 點擊「**確認加入 N 個行程**」按鈕
4. 系統會批次加入到 Google Calendar
5. 回到主頁面可看到新增的行程

### 5. 多模組 AI 對話

1. 點擊右上角「**💬 多模組 AI**」
2. 輸入 OpenAI 和 Gemini 的 API Key
3. 選擇模型 (gemini-2.0-flash-exp / gpt-3.5-turbo / gpt-4)
4. 輸入問題即可開始對話
5. Token 會自動保存到 SessionStorage

## 🔧 API 端點說明

### 天氣 API
```http
GET /api/weather?lat={緯度}&lon={經度}
```

### 餐廳推薦 API
```http
GET /api/food?locations={地點}&only_open={true/false}
```

### Gmail & Calendar 同步
```http
GET /api/sync-tasks?year={年}&month={月}
```

### 智慧郵件分析
```http
POST /api/smart-analysis
Content-Type: application/json

{
  "intent": "recent|today|unread",
  "email_count": 20,
  "remove_keywords": ["廣告", "促銷"],
  "custom_prompt": "AI 分析指示",
  "api_key": "your_api_key",
  "model_type": "gemini|openai"
}
```

### 批次加入行事曆
```http
POST /api/calendar/batch-add-events
Content-Type: application/json

{
  "events": [
    {
      "title": "事件標題",
      "date": "2025-12-27",
      "time": "14:00",
      "isAllDay": false,
      "description": "事件描述"
    }
  ]
}
```

### AI 對話 API
```http
POST /api/chat/gemini
POST /api/chat/openai
Content-Type: application/json

{
  "prompt": "你的問題",
  "model": "gemini-2.0-flash-exp|gpt-3.5-turbo",
  "api_key": "your_api_key"
}
```

## ⚙️ 環境變數配置

### 後端環境變數 (可選)

```bash
# .env (建立於 backend/ 資料夾)
GOOGLE_CREDENTIALS_PATH=credentials.json
TOKEN_PATH=token.json
```

### Docker Compose 配置

```yaml
# docker-compose.yml
services:
  backend:
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      
  frontend:
    ports:
      - "5173:80"
```

## 📊 功能限制與注意事項

### API 速率限制

| API | 免費配額 | 限制 |
|-----|---------|------|
| Gemini API | 10 請求/分鐘 | 1500 請求/天 |
| OpenAI API | 依方案而定 | 需付費使用 |
| Gmail API | 250 配額單位/秒 | 每日配額依用戶而定 |
| Calendar API | 1000 請求/100秒 | 每日配額 10,000 |

### 建議使用方式

1. **郵件數量**：
   - 建議一次分析 **10-15 封郵件**以獲得最佳體驗
   - 分析 33 封郵件約需 **3-4 分鐘**（因 Gemini 速率限制）

2. **批次處理**：
   - 系統會自動每 10 封郵件暫停 60 秒避免限流
   - OpenAI 有更高的速率限制但需付費

3. **Token 管理**：
   - API Keys 儲存在 SessionStorage，關閉分頁後會自動清除
   - 建議定期更換 API Key 以確保安全

4. **OAuth Token**：
   - Google OAuth token 會自動刷新
   - 如遇 401 錯誤，請重新連結 Google 帳號

## 🐛 常見問題排解

### 1. Docker 容器無法啟動

```bash
# 清除所有容器和映像
docker-compose down
docker system prune -f

# 重新建置
docker-compose build --no-cache
docker-compose up -d
```

### 2. 401 Unauthorized 錯誤

- 確認 `credentials.json` 正確放置於 `backend/` 資料夾
- 刪除 `token.json` 並重新授權
- 確認 Google Cloud Console 中的 API 已啟用

### 3. 郵件分析失敗 (404 模型錯誤)

- 確認使用最新版本的 `google-genai` 套件
- 檢查 API Key 是否有效
- 嘗試切換到 `gemini-2.0-flash-exp` 模型

### 4. 前端無法連接後端

```bash
# 檢查後端狀態
docker logs final-project-backend-1

# 確認後端正在運行
curl http://localhost:8000/api/weather
```

### 5. 日期格式錯誤

- 確保後端返回的日期格式為 `YYYY-MM-DD`
- 確保時間格式為 `HH:MM` 或 `null`
- 系統會自動處理無效值

## 📝 開發日誌

### v2.0.0 (2025-12-27)
- ✅ 切換到新的 `google-genai` 套件
- ✅ 修復 Token 自動刷新機制
- ✅ 改進顏色分配邏輯（避免重複）
- ✅ 修復日期時間 null 值處理
- ✅ 添加詳細的錯誤處理與提示

### v1.5.0
- ✅ 實作批次處理機制（避免 API 限流）
- ✅ 添加 AI 摘要生成功能
- ✅ 支援可自訂郵件數量 (1-100)
- ✅ SessionStorage 儲存 API Keys

### v1.0.0
- ✅ 基礎 Gmail & Calendar 整合
- ✅ 智慧郵件分析功能
- ✅ Docker 容器化部署
- ✅ 多模組 AI 對話



## 📄 授權

此專案僅供學術與教育用途。

## 🔗 相關連結

- [FastAPI 官方文件](https://fastapi.tiangolo.com/)
- [Vue 3 官方文件](https://vuejs.org/)
- [Google API Python Client](https://github.com/googleapis/google-api-python-client)
- [Gemini API 文件](https://ai.google.dev/)
- [OpenAI API 文件](https://platform.openai.com/docs)



⭐ 如果這個專案對你有幫助，請給個 Star！



