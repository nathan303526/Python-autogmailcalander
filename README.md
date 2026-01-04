# 📧 智慧郵件管理系統 (Smart Email & Calendar Manager)

一個結合 AI 智慧分析的郵件與行事曆管理系統，使用 Google Gmail API、Google Calendar API 以及 Gemini/OpenAI AI 模型，自動分析郵件內容並智慧地加入到 Google Calendar 中。

本系統具備完整的會員登入機制、雙重驗證 (2FA) 安全保護，以及個人化的 API Key 管理功能。

## 🎯 專案特色

### 核心功能
- **🔐 安全認證系統**：
  - 完整的註冊與登入機制 (JWT Token)
  - **雙重驗證 (2FA)**：支援 Google Authenticator (TOTP)
  - 密碼加密儲存 (Bcrypt)
- **👤 個人化設定**：
  - 個人資料管理 (姓名、Email)
  - **API Key 雲端儲存**：可將 OpenAI/Gemini Key 存入資料庫，跨裝置使用
  - 密碼變更功能
- **🧠 AI 智慧郵件分析**：使用 Gemini 或 OpenAI 自動判斷郵件是否需要加入行事曆
- **📅 自動日曆管理**：智慧提取郵件中的日期、時間資訊並加入 Calendar
- **🔄 Google 整合**：OAuth 2.0 授權連結 Gmail 與 Google Calendar

### 輔助功能
- **🗄️ 資料庫管理**：內建 Adminer 資料庫管理介面，方便檢視後端資料
- **🌤️ 天氣查詢**：顯示當前位置天氣資訊
- **🍽️ 餐廳推薦**：隨機推薦附近餐廳
- **💬 多模組 AI 對話**：支援 Gemini 和 OpenAI 多模型對話

## 🛠️ 技術架構

### 後端 (Backend)
- **框架**: FastAPI (Python 3.11)
- **資料庫**: MariaDB (Docker Container)
- **ORM**: SQLAlchemy
- **認證**: Python-JOSE (JWT), Passlib (Bcrypt), PyOTP (2FA)
- **AI 模型**: Google Gemini API, OpenAI GPT API
- **Google API**: Gmail API (v1), Google Calendar API (v3)

### 前端 (Frontend)
- **框架**: Vue 3 (Composition API)
- **UI**: Tailwind CSS
- **HTTP 客戶端**: Axios
- **建置工具**: Vite

### DevOps
- **容器化**: Docker Compose (Backend, Frontend, Database, Adminer)
- **資料庫管理**: Adminer (Web GUI)

## 📦 專案結構

```
期末專題/
├── backend/                 # FastAPI 後端
│   ├── main.py             # 主程式 (API 路由 & DB Model)
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
│   │   │   ├── LoginModal.vue       # 登入/註冊/2FA 視窗
│   │   │   ├── ProfileSettings.vue  # 個人資料設定
│   │   │   ├── SmartAnalysis.vue    # 智慧分析主組件
│   │   │   └── ...
│   │   ├── App.vue         # 根組件
│   │   └── main.js         # 入口文件
│   ├── package.json        # Node.js 依賴
│   ├── vite.config.js      # Vite 配置
│   └── Dockerfile          # 前端容器配置
│
├── docker-compose.yml      # Docker Compose 配置 (含 MariaDB & Adminer)
└── README.md               # 專案說明文件
```

## 🚀 快速開始

### 前置需求

1. **Docker & Docker Compose** (推薦)
   - Docker Desktop 4.0+
2. **Google API 憑證**
   - 下載 `credentials.json` 並放入 `backend/` 資料夾
3. **AI API Keys** (Gemini / OpenAI)

### Docker 部署 (推薦)

```bash
# 1. 克隆專案
git clone <repository-url>
cd 期末專題

# 2. 確保 credentials.json 已放入 backend/

# 3. 啟動所有服務 (後端、前端、資料庫、Adminer)
docker-compose up -d

# 4. 查看日誌 (確認資料庫連線成功)
docker-compose logs -f backend
```

服務將會啟動於：
- **前端**: http://localhost:5173
- **後端 API**: http://localhost:8000
- **API 文件**: http://localhost:8000/docs
- **資料庫管理 (Adminer)**: http://localhost:8080

### 預設管理員帳號

系統啟動時會自動建立預設管理員帳號：
- **帳號**: `admin`
- **密碼**: `secret`

請登入後立即修改密碼！

## 📖 使用指南

### 1. 登入與安全設定
1. 打開首頁，點擊登入。
2. 使用預設帳號 `admin` / `secret` 登入，或註冊新帳號。
3. 登入後，點擊右上角 **「啟用 2FA」**。
4. 使用 Google Authenticator 掃描 QR Code，輸入驗證碼完成設定。
5. 下次登入時將需要輸入 2FA 驗證碼。

### 2. 個人資料與 API Key
1. 點擊右上角 **「設定」** 按鈕。
2. 在 **「個人資料 & API Key」** 分頁中，輸入您的 OpenAI 或 Gemini API Key。
3. 儲存後，系統進行 AI 分析時將優先使用您個人的 API Key。
4. 在 **「修改密碼」** 分頁中可隨時變更登入密碼。

### 3. Google 授權連結
1. 點擊左側選單的 **「同步 Gmail & Calendar」**。
2. 授權應用程式存取您的 Google 帳號。

### 4. 智慧郵件分析
1. 點擊 **「🧠 智慧分析」**。
2. 選擇 AI 模型與分析範圍。
3. 若已在個人設定中儲存 API Key，此處可留空；否則需手動輸入。
4. 點擊 **「開始智慧分析」**，系統將自動篩選郵件並建議行事曆行程。

### 5. 資料庫管理 (Adminer)
1. 前往 http://localhost:8080
2. 系統選擇: `MySQL`
3. 伺服器: `db`
4. 使用者: `root`
5. 密碼: `secret`
6. 資料庫: `final_project`

## 🔧 API 端點說明

### 認證 API
```http
POST /api/auth/register      # 註冊
POST /api/auth/login         # 登入 (回傳 JWT)
GET  /api/auth/2fa/setup     # 取得 2FA QR Code
POST /api/auth/2fa/verify    # 驗證 2FA
```

### 使用者 API
```http
GET /api/users/me            # 取得個人資料
PUT /api/users/me            # 更新個人資料 (含 API Key)
PUT /api/users/me/password   # 修改密碼
```

### 智慧分析 API
```http
POST /api/smart-analysis
Content-Type: application/json

{
  "intent": "recent",
  "email_count": 20,
  "remove_keywords": ["廣告"],
  "custom_prompt": "...",
  "api_key": "...",  # 若未提供，則使用使用者資料庫中的 Key
  "model_type": "gemini"
}
```

## ⚙️ 環境變數配置

### Docker Compose 配置

```yaml
services:
  backend:
    environment:
      - DATABASE_URL=mysql+pymysql://root:secret@db:3306/final_project
  db:
    image: mariadb:10.6
    environment:
      - MYSQL_ROOT_PASSWORD=secret
      - MYSQL_DATABASE=final_project
```

## 🐛 常見問題排解

### 1. 資料庫連線失敗
- 確認 `db` 容器已啟動 (`docker-compose ps`)。
- 若剛啟動，後端可能會重試連線幾次，請稍等。

### 2. 2FA 驗證失敗 (400 Bad Request)
- 確保手機時間與電腦時間同步。
- 2FA 驗證碼時效為 30 秒，請在時效內輸入。

### 3. API Key 無法使用
- 請確認在「設定」頁面中輸入的 Key 正確無誤。
- 若設定頁面留空，則需在每次分析時手動輸入。

## 📄 授權

此專案僅供學術與教育用途。
