from fastapi import FastAPI, Query, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import random
import time
import httpx
import openai
import os
import json
from google import genai
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# Google OAuth 設定存放路徑
CREDENTIALS_PATH = "credentials.json"
TOKEN_PATH = "token.json"

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "*" 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/weather")
async def get_weather(lat: float = 24.95, lon: float = 121.22):
    print(f"收到氣象請求: lat={lat}, lon={lon}") 
    
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code&timezone=auto"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0) # 設定 Timeout 避免卡死
            print(f"外部 API 回應狀態: {response.status_code}") # Debug Log
            
            response.raise_for_status() # 檢查是否成功
            data = response.json()
            
            # 解析資料
            temp = data["current"]["temperature_2m"]
            wmo_code = data["current"]["weather_code"]
            

            status = "晴天"
            if wmo_code > 3: status = "多雲"
            if wmo_code > 50: status = "有雨"
            if wmo_code > 80: status = "雷雨"
            if wmo_code > 95: status = "下雪"


            location_name = "您的位置"
            if abs(lat - 24.95) < 0.01 and abs(lon - 121.22) < 0.01:
                location_name = "中壢 (預設)"

            result = {
                "location": location_name,
                "temperature": temp,
                "status": status,
                "description": f"目前氣溫 {temp}°C，出門請留意"
            }
            return result

    except Exception as e:
        print(f"Error fetching weather: {e}")
        import traceback
        traceback.print_exc() # 印出完整錯誤堆疊
        
        # 發生錯誤時回傳備用資料
        return {
            "location": "中壢 (備用)",
            "temperature": 24,
            "status": "未知",
            "description": "暫時無法取得氣象資料"
        }

# 資料庫模擬
from data import restaurants_db

def is_open(restaurant):
    now = datetime.now()
    current_day = (now.weekday() + 1) % 7 
    current_time = now.strftime("%H:%M")

    for schedule in restaurant.get("openingHours", []):
        if current_day in schedule["days"]:
            for slot in schedule["slots"]:
                if slot["start"] <= current_time <= slot["end"]:
                    return True
    return False

# API 2: /api/food
@app.get("/api/food")
def get_food(locations: List[str] = Query(default=["後門"]), only_open: bool = False):
    # 1. 篩選地點
    candidates = [r for r in restaurants_db if r["location"] in locations]
    
    # 2. 篩選營業時間
    if only_open:
        candidates = [r for r in candidates if is_open(r)]
    
    if not candidates:
        return {"error": "沒有符合條件的餐廳", "food": None}

    choice = random.choice(candidates)
    return {
        "food": choice["name"],
        "address": choice["address"],
        "businesshours": choice["businesshours"],
        "location": choice["location"]
    }

# 定義 Task 模型
class Task(BaseModel):
    title: str
    action: str
    status: str

# API 3: /api/sync-tasks (核心功能)
@app.get("/api/sync-tasks", response_model=List[Task])
def sync_tasks():
    # 模擬 AI 分析的延遲感
    time.sleep(2)
    
    # ---------------------------------------------------------
    # (註解：若要接真實 Google API 請修改此處)
    # 例如：
    # 1. 接收前端傳來的 token
    # 2. 呼叫 Google Calendar API 取得事件
    # 3. 使用 LLM 分析事件並產生建議 action
    # ---------------------------------------------------------

    # 模擬回傳 3 筆「假」的分析結果
    mock_results = [
        {"title": "交作業", "action": "加入行事曆", "status": "success"},
        {"title": "專題討論", "action": "設定提醒", "status": "success"},
        {"title": "買晚餐", "action": "加入待辦清單", "status": "pending"}
    ]
    
    return mock_results

class ChatRequest(BaseModel):
    prompt: str
    api_key: str
    model: str

@app.post("/api/chat/openai")
async def chat_openai(request: ChatRequest):
    try:
        client = openai.AsyncOpenAI(api_key=request.api_key)
        response = await client.chat.completions.create(
            model=request.model,
            messages=[{"role": "user", "content": request.prompt}]
        )
        return {"response": response.choices[0].message.content}
    except Exception as e:
        print(f"OpenAI Error: {e}")
        return {"error": str(e)}

@app.post("/api/chat/gemini")
async def chat_gemini(request: ChatRequest):
    try:
        client = genai.Client(api_key=request.api_key)

        model_name = request.model if request.model.startswith('models/') else f'models/{request.model}'
        
        response = await client.aio.models.generate_content(
            model=model_name,
            contents=request.prompt
        )
        return {"response": response.text}
    except Exception as e:
        print(f"Gemini Error: {e}")
        return {"error": str(e)}

# Google OAuth 相關 API
@app.post("/api/google/upload-credentials")
async def upload_credentials(file: UploadFile = File(...)):
    try:

        if not file.filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="請上傳 JSON 格式的檔案")
        
        content = await file.read()
        
        try:
            data = json.loads(content)
            if 'installed' not in data and 'web' not in data:
                raise HTTPException(status_code=400, detail="無效的 client_secret.json 格式")
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="無效的 JSON 檔案")
            
        # 儲存檔案
        with open(CREDENTIALS_PATH, "wb") as f:
            f.write(content)
            
        return {"status": "success", "message": "憑證上傳成功"}
        
    except Exception as e:
        print(f"Upload Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/google/status")
def get_google_status():
    return {
        "configured": os.path.exists(CREDENTIALS_PATH),
        "authenticated": os.path.exists(TOKEN_PATH)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
