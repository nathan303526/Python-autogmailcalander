# 期末專題 - 智慧待辦助理 Dashboard

這是一個結合 Vue 3 前端與 Python FastAPI 後端的全端專案。

## 專案架構

- `backend/`: Python FastAPI 後端 API
- `frontend/`: Vue 3 + Tailwind CSS 前端介面

## 環境需求

- Python 3.8+
- Node.js 16+

## 快速啟動指南

請開啟兩個終端機 (Terminal)，分別執行後端與前端。

### 1. 啟動後端 (Backend)

在第一個終端機中執行：

```bash
# 進入後端資料夾
cd backend

# 建立虛擬環境 (若已建立可跳過)
python -m venv .venv

# 啟動虛擬環境 (Windows)
.venv\Scripts\Activate
# 啟動虛擬環境 (Mac/Linux)
# source .venv/bin/activate

# 安裝套件
pip install -r requirements.txt

# 啟動伺服器
python main.py
```

後端伺服器將啟動於：`http://localhost:8000`
API 文件 (Swagger UI)：`http://localhost:8000/docs`

### 2. 啟動前端 (Frontend)

在第二個終端機中執行：

```bash
# 進入前端資料夾
cd frontend

# 安裝相依套件 (初次執行需要)
npm install

# 啟動開發伺服器
npm run dev
```

前端頁面將啟動於：`http://localhost:5173`

## 功能說明

1.  **天氣小卡**：呼叫 `/api/weather` 顯示模擬天氣。
2.  **午餐抽籤**：呼叫 `/api/food` 隨機決定午餐。
3.  **智慧同步**：呼叫 `/api/sync-tasks` 模擬 AI 分析待辦事項 (有 2 秒延遲效果)。



