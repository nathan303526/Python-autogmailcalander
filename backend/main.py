from fastapi import FastAPI, Query, UploadFile, File, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
import random
import time
import asyncio
import httpx
import openai
import os
import json
import re
from google import genai
from google.genai import types
from google_auth_oauthlib.flow import InstalledAppFlow
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import StreamingResponse
from jose import JWTError, jwt
from passlib.context import CryptContext
import pyotp
import io
import qrcode
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# 引入 OAuth 模組
import Oauth

app = FastAPI()

# --- 資料庫設定 (MariaDB) ---
# 優先讀取環境變數 (Docker)，否則使用 localhost (本機開發)
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:secret@localhost:3306/final_project")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 資料庫模型 ---
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    hashed_password = Column(String(100))
    secret_2fa = Column(String(32), nullable=True)
    is_2fa_enabled = Column(Boolean, default=False)
    
    # 新增欄位
    full_name = Column(String(100), nullable=True)
    email = Column(String(100), nullable=True)
    openai_api_key = Column(String(200), nullable=True)
    gemini_api_key = Column(String(200), nullable=True)

# 等待資料庫連線並建立資料表
def init_db(retries=5, delay=5):
    for i in range(retries):
        try:
            Base.metadata.create_all(bind=engine)
            print("Database connected and tables created.")
            return
        except Exception as e:
            print(f"Database connection failed (attempt {i+1}/{retries}): {e}")
            if i < retries - 1:
                time.sleep(delay)
            else:
                print("Could not connect to database after multiple attempts.")

# 在啟動時執行
init_db()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 安全性設定 ---
# 在生產環境中，請務必透過環境變數設定 SECRET_KEY，不要使用預設值
SECRET_KEY = os.getenv("SECRET_KEY", "YOUR_SUPER_SECRET_KEY_CHANGE_THIS") 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# 初始化預設 Admin 帳號
try:
    db = SessionLocal()
    admin_user = db.query(User).filter(User.username == "admin").first()
    if not admin_user:
        print("Creating default admin user...")
        default_password = os.getenv("ADMIN_PASSWORD", "secret")
        hashed_password = pwd_context.hash(default_password)
        new_user = User(username="admin", hashed_password=hashed_password)
        db.add(new_user)
        db.commit()
        print(f"Default admin user created: admin / {default_password}")
    db.close()
except Exception as e:
    print(f"Error creating default admin: {e}")

class Token(BaseModel):
    access_token: str
    token_type: str

class Verify2FARequest(BaseModel):
    username: str
    code: str

# 新增註冊用的 Model
class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    full_name: Optional[str] = None

class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None

class PasswordUpdate(BaseModel):
    old_password: str
    new_password: str

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# Google OAuth 設定存放路徑
CREDENTIALS_PATH = "credentials.json"
TOKEN_PATH = "token.json"

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    # "*", # 生產環境建議移除此行，只允許特定網域
]

# 如果有設定 FRONTEND_URL 環境變數，則加入該網域
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 登入與 2FA API ---

@app.post("/api/auth/register", response_model=Token)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # 檢查帳號是否已存在
    db_user = db.query(User).filter(User.username == user_data.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # 建立新使用者
    hashed_password = pwd_context.hash(user_data.password)
    new_user = User(
        username=user_data.username, 
        hashed_password=hashed_password,
        email=user_data.email,
        full_name=user_data.full_name
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # 自動登入
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/auth/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/auth/2fa/setup")
async def setup_2fa(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    secret = pyotp.random_base32()
    
    # 更新使用者資料庫
    current_user.secret_2fa = secret
    db.commit()
    
    uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=current_user.username, 
        issuer_name="GmailCalander"
    )
    
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)
    
    return StreamingResponse(buf, media_type="image/png")

@app.post("/api/auth/2fa/verify")
async def verify_2fa(request: Verify2FARequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == request.username).first()
    if not user or not user.secret_2fa:
        raise HTTPException(status_code=400, detail="2FA not setup for this user")

    totp = pyotp.TOTP(user.secret_2fa)
    if totp.verify(request.code, valid_window=1):
        user.is_2fa_enabled = True
        db.commit()
        return {"status": "success", "message": "2FA verified and enabled"}
    else:
        raise HTTPException(status_code=400, detail="Invalid 2FA code")

@app.get("/api/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return {
        "username": current_user.username,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "2fa_enabled": current_user.is_2fa_enabled,
        "has_openai_key": bool(current_user.openai_api_key),
        "has_gemini_key": bool(current_user.gemini_api_key)
    }

@app.put("/api/users/me")
async def update_user_me(user_update: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    if user_update.email is not None:
        current_user.email = user_update.email
    if user_update.openai_api_key is not None:
        current_user.openai_api_key = user_update.openai_api_key
    if user_update.gemini_api_key is not None:
        current_user.gemini_api_key = user_update.gemini_api_key
    
    db.commit()
    db.refresh(current_user)
    return {"status": "success", "message": "Profile updated"}

@app.put("/api/users/me/password")
async def update_password(password_update: PasswordUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not pwd_context.verify(password_update.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect old password")
    
    current_user.hashed_password = pwd_context.hash(password_update.new_password)
    db.commit()
    return {"status": "success", "message": "Password updated"}


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


from data import restaurants_db

def is_open(restaurant):
    tz = timezone(timedelta(hours=8))
    now = datetime.now(tz)
    current_day = (now.weekday() + 1) % 7 
    prev_day = (current_day - 1 + 7) % 7
    current_time = now.strftime("%H:%M")

    for schedule in restaurant.get("openingHours", []):
        # 檢查今天的營業時間
        if current_day in schedule["days"]:
            for slot in schedule["slots"]:
                start, end = slot["start"], slot["end"]
                if start <= end:
                    if start <= current_time <= end:
                        return True
                else:
                    if current_time >= start:
                        return True
        
        # (是否跨日到今天凌晨)
        if prev_day in schedule["days"]:
            for slot in schedule["slots"]:
                start, end = slot["start"], slot["end"]
                if start > end:
                    if current_time <= end:
                        return True
                        
    return False

# API 2: /api/food
@app.get("/api/food")
def get_food(locations: List[str] = Query(default=["後門"]), only_open: bool = False):
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

# API 3: /api/sync-tasks (核心功能)
@app.get("/api/sync-tasks")
def sync_tasks(year: Optional[int] = None, month: Optional[int] = None):
    # 嘗試取得 Google 服務
    gmail_service = Oauth.get_gmail_service()
    calendar_service = Oauth.get_calendar_service()
    
    # 檢查授權狀態
    if not gmail_service and not calendar_service:
        raise HTTPException(status_code=401, detail="Unauthorized - Please authenticate with Google first")
    
    gmail_data = []
    calendar_data = []
    calendar_next_token = None

    # 1. 讀取 Gmail 
    if gmail_service:
        try:
            results = gmail_service.users().messages().list(userId='me', maxResults=20).execute()
            messages = results.get('messages', [])
            for msg in messages:
                txt = gmail_service.users().messages().get(userId='me', id=msg['id']).execute()
                payload = txt.get('payload', {})
                headers = payload.get('headers', [])
                snippet = txt.get('snippet', '')
                
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(無主旨)')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), '(未知寄件者)')
                date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
                
                clean_snippet = ' '.join(snippet.split())
                
                gmail_data.append({
                    "id": msg['id'],
                    "subject": subject,
                    "sender": sender,
                    "snippet": clean_snippet,
                    "date": date
                })
        except Exception as e:
            print(f"Gmail Error: {e}")
            gmail_data.append({"subject": "讀取錯誤", "sender": "System", "snippet": str(e)})


    if calendar_service:
        try:
            now = datetime.utcnow()
            target_year = year if year else now.year
            target_month = month if month else now.month
            
            # 計算該月的第一天和下個月的第一天
            start_of_month = datetime(target_year, target_month, 1)
            if target_month == 12:
                next_month = datetime(target_year + 1, 1, 1)
            else:
                next_month = datetime(target_year, target_month + 1, 1)
            
            timeMin = start_of_month.isoformat() + 'Z'
            timeMax = next_month.isoformat() + 'Z'
            
            events_result = calendar_service.events().list(
                calendarId='primary', 
                timeMin=timeMin,
                timeMax=timeMax,
                maxResults=250,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            calendar_next_token = events_result.get('nextPageToken')
            
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                calendar_data.append({
                    "id": event.get('id'),
                    "summary": event.get('summary', '(無標題)'),
                    "start": start,
                    "end": end,
                    "description": event.get('description', '')
                })
        except Exception as e:
            print(f"Calendar Error: {e}")
            calendar_data.append({"summary": "讀取錯誤", "start": "", "end": "", "description": str(e)})
    
    # 如果都沒有授權，回傳 401 讓前端重新授權
    if not gmail_service and not calendar_service:
        raise HTTPException(status_code=401, detail="需要重新授權")

    return {
        "gmail": gmail_data,
        "calendar": calendar_data,
        "calendarNextPageToken": calendar_next_token
    }

class LoadMoreRequest(BaseModel):
    pageToken: str

@app.post("/api/calendar/load-more")
def load_more_calendar(request: LoadMoreRequest):
    calendar_service = Oauth.get_calendar_service()
    if not calendar_service:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        # 載入更多 (不設時間限制，或者延續之前的邏輯? 通常 pageToken 會延續之前的 query 條件)
        # 但為了保險起見，我們只依賴 pageToken
        events_result = calendar_service.events().list(
            calendarId='primary',
            pageToken=request.pageToken,
            maxResults=20,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        next_token = events_result.get('nextPageToken')
        
        calendar_data = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            calendar_data.append({
                "id": event.get('id'),
                "summary": event.get('summary', '(無標題)'),
                "start": start,
                "end": end,
                "description": event.get('description', '')
            })
            
        return {
            "calendar": calendar_data,
            "calendarNextPageToken": next_token
        }
    except Exception as e:
        print(f"Load More Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class ChatRequest(BaseModel):
    prompt: str
    api_key: Optional[str] = None # 改為 Optional
    model: str

@app.post("/api/chat/openai")
async def chat_openai(request: ChatRequest, current_user: User = Depends(get_current_user)):
    # 優先使用使用者的 API Key
    api_key = current_user.openai_api_key or request.api_key
    
    if not api_key:
        raise HTTPException(status_code=400, detail="OpenAI API Key is required (set in profile or request)")

    try:
        client = openai.AsyncOpenAI(api_key=api_key)
        response = await client.chat.completions.create(
            model=request.model,
            messages=[{"role": "user", "content": request.prompt}]
        )
        return {"response": response.choices[0].message.content}
    except Exception as e:
        print(f"OpenAI Error: {e}")
        return {"error": str(e)}

@app.post("/api/chat/gemini")
async def chat_gemini(request: ChatRequest, current_user: User = Depends(get_current_user)):
    # 優先使用使用者的 API Key
    api_key = current_user.gemini_api_key or request.api_key
    
    if not api_key:
        raise HTTPException(status_code=400, detail="Gemini API Key is required (set in profile or request)")

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=request.model,
            contents=request.prompt
        )
        return {"response": response.text}
    except Exception as e:
        print(f"Gemini Error: {e}")
        return {"error": str(e)}

# Google OAuth 相關 API

class GoogleSetupRequest(BaseModel):
    client_id: str
    client_secret: str

class GoogleCallbackRequest(BaseModel):
    code: str

@app.post("/api/google/setup")
async def google_setup(request: GoogleSetupRequest):
    try:
        # 建構 client_config
        client_config = {
            "installed": {
                "client_id": request.client_id,
                "client_secret": request.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
            }
        }
        
        # 儲存 credentials.json
        with open(CREDENTIALS_PATH, "w") as f:
            json.dump(client_config, f)
            
        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_PATH, 
            scopes=Oauth.SCOPES,
            redirect_uri='urn:ietf:wg:oauth:2.0:oob'
        )
        
        auth_url, _ = flow.authorization_url(prompt='consent')
        
        return {"auth_url": auth_url}
        
    except Exception as e:
        print(f"Setup Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/google/callback")
async def google_callback(request: GoogleCallbackRequest):
    try:
        if not os.path.exists(CREDENTIALS_PATH):
            raise HTTPException(status_code=400, detail="請先設定 Client ID/Secret")
            
        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_PATH, 
            scopes=Oauth.SCOPES,
            redirect_uri='urn:ietf:wg:oauth:2.0:oob'
        )
        
        # 交換 Token
        flow.fetch_token(code=request.code)
        creds = flow.credentials
        
        # 儲存 token.json
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
            
        return {"status": "success", "message": "授權成功"}
        
    except Exception as e:
        print(f"Callback Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/google/status")
def get_google_status():
    return {
        "configured": os.path.exists(CREDENTIALS_PATH),
        "authenticated": os.path.exists(TOKEN_PATH)
    }

# 新增行事曆事件
class AddEventRequest(BaseModel):
    summary: str
    start: str  # ISO 8601 format: 2025-12-27T14:00:00
    description: str = ""

@app.post("/api/calendar/add-event")
def add_calendar_event(request: AddEventRequest):
    calendar_service = Oauth.get_calendar_service()
    if not calendar_service:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        # 解析開始時間，結束時間默認為開始時間 + 1 小時
        start_dt = datetime.fromisoformat(request.start)
        end_dt = start_dt + timedelta(hours=1)
        
        event = {
            'summary': request.summary,
            'description': request.description,
            'start': {
                'dateTime': start_dt.isoformat(),
                'timeZone': 'Asia/Taipei',
            },
            'end': {
                'dateTime': end_dt.isoformat(),
                'timeZone': 'Asia/Taipei',
            },
        }
        
        result = calendar_service.events().insert(calendarId='primary', body=event).execute()
        
        return {"success": True, "event_id": result.get('id')}
    except Exception as e:
        print(f"Add Event Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/calendar/delete-event/{event_id}")
def delete_calendar_event(event_id: str):
    calendar_service = Oauth.get_calendar_service()
    if not calendar_service:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        calendar_service.events().delete(calendarId='primary', eventId=event_id).execute()
        return {"success": True, "message": "已刪除行程"}
    except Exception as e:
        print(f"Delete Event Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 智慧分析請求模型
class SmartAnalysisRequest(BaseModel):
    intent: str  # recent, today, unread
    email_count: Optional[int] = 20  # 當 intent 為 recent 時使用
    add_keywords: List[str]
    remove_keywords: List[str]
    custom_prompt: str
    api_key: str
    model_type: str = "gemini"  # "gemini" or "openai"

# 批量添加事件請求模型
class BatchEventRequest(BaseModel):
    title: str
    date: str
    time: Optional[str] = None
    isAllDay: Optional[bool] = False
    description: str

class BatchAddEventsRequest(BaseModel):
    events: List[BatchEventRequest]

@app.post("/api/smart-analysis")
async def smart_analysis(request: SmartAnalysisRequest):
    gmail_service = Oauth.get_gmail_service()
    if not gmail_service:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        # 1. 根據意圖獲取郵件
        if request.intent == "recent":
            max_results = min(request.email_count or 20, 100)  # 限制最多 100 封
            print(f"[DEBUG] 請求獲取最近 {max_results} 封郵件")
            results = gmail_service.users().messages().list(userId='me', maxResults=max_results).execute()
        elif request.intent == "today":
            today = datetime.now().strftime('%Y/%m/%d')
            results = gmail_service.users().messages().list(
                userId='me', 
                q=f'after:{today}',
                maxResults=50
            ).execute()
        elif request.intent == "unread":
            results = gmail_service.users().messages().list(
                userId='me', 
                q='is:unread',
                maxResults=50
            ).execute()
        else:
            results = gmail_service.users().messages().list(userId='me', maxResults=20).execute()
        
        messages = results.get('messages', [])
        print(f"[DEBUG] Gmail API 實際返回 {len(messages)} 封郵件")
        
        # 2. 獲取完整郵件資訊
        emails = []
        for msg in messages:
            msg_data = gmail_service.users().messages().get(userId='me', id=msg['id']).execute()
            headers = msg_data['payload']['headers']
            
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            date_str = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            snippet = msg_data.get('snippet', '')
            snippet = re.sub(r'\s+', ' ', snippet).strip()
            
            emails.append({
                'id': msg['id'],
                'subject': subject,
                'snippet': snippet,
                'date': date_str
            })
        
        # 3. 關鍵字篩選
        matched = []  # AI 分析後符合的
        removed = []  # 符合移除關鍵字的
        pending = []  # 需要LLM判斷的
        
        print(f"[DEBUG] 開始關鍵字篩選，移除關鍵字: {request.remove_keywords}")
        
        for email in emails:
            text = (email['subject'] + ' ' + email['snippet']).lower()
            
            # 檢查移除關鍵字
            if any(kw.lower() in text for kw in request.remove_keywords if kw):
                removed.append(email)
                continue
            
            # 所有其他郵件都交給 AI 分析
            pending.append(email)
        
        print(f"[DEBUG] 關鍵字篩選結果: 移除 {len(removed)} 封，待 AI 分析 {len(pending)} 封")
        
        # 4. LLM分析待定郵件
        if pending and request.api_key:
            print(f"[DEBUG] 開始 AI 分析 {len(pending)} 封郵件")
            llm_results, removed_by_ai = await analyze_with_llm(pending, request.custom_prompt, request.api_key, request.model_type)
            print(f"[DEBUG] AI 分析完成: {len(llm_results)} 封符合，{len(removed_by_ai)} 封被 AI 移除")
            for result in llm_results:
                if result['confidence'] > 0.75:
                    matched.append(result)
            
            print(f"[DEBUG] 信心指數篩選後: {len(matched)} 封將加入")
            
            # 將 AI 判斷移除的郵件加入 removed 列表
            for item in removed_by_ai:
                removed.append({
                    **item['email'],
                    'removeReason': item['reason'],
                    'confidence': item['confidence']
                })
        
        # 5. 檢查日曆衝突（將有衝突的放入 pending）
        calendar_service = Oauth.get_calendar_service()
        pending_conflicts = []
        
        if calendar_service:
            for match in matched[:]:
                # 檢查該日期是否已有事件
                try:
                    date_str = match['suggestedDate']
                    time_min = f"{date_str}T00:00:00+08:00"
                    time_max = f"{date_str}T23:59:59+08:00"
                    
                    events_result = calendar_service.events().list(
                        calendarId='primary',
                        timeMin=time_min,
                        timeMax=time_max,
                        singleEvents=True,
                        orderBy='startTime'
                    ).execute()
                    
                    existing_events = events_result.get('items', [])
                    
                    if existing_events:
                        # 有衝突，移到 pending
                        pending_conflicts.append({
                            **match,
                            'conflictEvents': [{
                                'summary': evt.get('summary', '無標題'),
                                'start': evt['start'].get('dateTime', evt['start'].get('date', ''))
                            } for evt in existing_events]
                        })
                        matched.remove(match)
                except Exception as e:
                    print(f"Calendar check error: {e}")
                    continue
        
        # 5. 生成 AI 摘要
        summary = ""
        if request.api_key and (matched or removed or pending_conflicts):
            try:
                summary = await generate_summary(
                    len(emails),
                    len(matched),
                    len(removed),
                    len(pending_conflicts),
                    matched,
                    removed,
                    request.api_key,
                    request.model_type
                )
            except Exception as e:
                print(f"Summary generation error: {e}")
                summary = f"分析完成！共讀取 {len(emails)} 封郵件。"
        
        return {
            'matched': matched,
            'removed': removed,
            'pending': pending_conflicts,
            'summary': summary
        }
        
    except Exception as e:
        print(f"Smart Analysis Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def extract_date_from_email(email):
    """嘗試從郵件中提取日期，如果沒有則返回郵件發送日期"""
    text = email['subject'] + ' ' + email['snippet']
    
    # 常見日期格式
    patterns = [
        r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # 2024-12-27
        r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # 12/27/2024
        r'(\d{1,2})月(\d{1,2})日',              # 12月27日
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                if '月' in pattern:
                    month, day = match.groups()
                    year = datetime.now().year
                    return f"{year}-{int(month):02d}-{int(day):02d}"
                elif match.group(1).isdigit() and len(match.group(1)) == 4:
                    # YYYY-MM-DD
                    return f"{match.group(1)}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"
                else:
                    # MM/DD/YYYY
                    return f"{match.group(3)}-{int(match.group(1)):02d}-{int(match.group(2)):02d}"
            except:
                pass
    
    # 沒有找到日期，嘗試從郵件日期欄位提取
    try:
        if 'date' in email and email['date']:
            # 解析郵件日期字符串
            from email.utils import parsedate_to_datetime
            email_date = parsedate_to_datetime(email['date'])
            return email_date.strftime('%Y-%m-%d')
    except:
        pass
    
    # 如果都失敗，返回今天
    today = datetime.now()
    return today.strftime('%Y-%m-%d')

def extract_time_from_email(email):
    """嘗試從郵件中提取時間，如果沒有則返回 None（全天事件）"""
    text = email['subject'] + ' ' + email['snippet']
    
    # 常見時間格式
    time_patterns = [
        r'(\d{1,2}):(\d{2})',  # 14:30
        r'(\d{1,2})點',         # 14點
        r'上午(\d{1,2})[點:]',  # 上匈9點
        r'下午(\d{1,2})[點:]',  # 下匈2點
    ]
    
    for pattern in time_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                if '上午' in pattern:
                    hour = int(match.group(1))
                    return f"{hour:02d}:00"
                elif '下午' in pattern:
                    hour = int(match.group(1))
                    if hour < 12:
                        hour += 12
                    return f"{hour:02d}:00"
                elif ':' in match.group(0):
                    hour = int(match.group(1))
                    minute = int(match.group(2))
                    return f"{hour:02d}:{minute:02d}"
                else:
                    hour = int(match.group(1))
                    return f"{hour:02d}:00"
            except:
                continue
    
    # 沒有找到時間，返回 None（將設為全天事件）
    return None

async def generate_summary(total_emails, matched_count, removed_count, pending_count, matched_emails, removed_emails, api_key, model_type="gemini"):
    """生成郵件分析摘要"""
    try:
        # 準備郵件標題列表
        matched_titles = [m['email']['subject'] for m in matched_emails[:5]]  # 只取前5個
        removed_titles = [r.get('subject', '') for r in removed_emails[:3]]  # 只取前3個
        
        prompt = f"""請簡潔地整理以下郵件分析結果的重點（不超過 150 字）：

總共分析了 {total_emails} 封郵件
- {matched_count} 封將加入日曆
- {removed_count} 封被移除
- {pending_count} 封有時間衝突

將加入的郵件主題：
{chr(10).join([f'- {t}' for t in matched_titles])}

被移除的郵件主題：
{chr(10).join([f'- {t}' for t in removed_titles]) if removed_titles else '無'}

請用 2-3 句話總結重點，例如主要的事件類型、重要的事項等。直接輸出摘要內容，不要前置說明。
"""
        
        if model_type == "gemini":
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents=prompt
            )
            return response.text.strip()
        else:
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一個專業的郵件分析助理。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=200
            )
            return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Summary generation error: {e}")
        return f"📊 分析完成！共 {matched_count} 封郵件將加入日曆，{removed_count} 封被過濾。"

async def analyze_with_llm(emails, custom_prompt, api_key, model_type="gemini"):
    """使用 Gemini 或 OpenAI 分析郵件"""
    results = []
    removed_by_ai = []  # AI 判斷不需要加入的郵件
    
    # 批次處理以避免限流
    batch_size = 10 if model_type == "gemini" else 20
    batch_delay = 60 if model_type == "gemini" else 10  # Gemini 每分鐘最多 10 個請求
    
    for i, email in enumerate(emails):
        try:
            if model_type == "gemini":
                # 使用 Gemini API
                client = genai.Client(api_key=api_key)
                
                prompt = f"""{custom_prompt}

請分析以下郵件:
主旨: {email['subject']}
內容: {email['snippet']}

請以JSON格式回覆:
{{
    "should_add": true/false,
    "confidence": 0.0-1.0,
    "suggested_date": "YYYY-MM-DD",
    "suggested_time": "HH:MM" (如果郵件中沒有明確時間，請設為 null),
    "reason": "判斷理由"
}}
"""
                
                response = client.models.generate_content(
                    model='gemini-2.0-flash-exp',
                    contents=prompt
                )
                content = response.text
                
            else:
                # 使用 OpenAI API
                client = openai.OpenAI(api_key=api_key)
                
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": custom_prompt},
                        {"role": "user", "content": f"""
請分析以下郵件:
主旨: {email['subject']}
內容: {email['snippet']}

請以JSON格式回覆:
{{
    "should_add": true/false,
    "confidence": 0.0-1.0,
    "suggested_date": "YYYY-MM-DD",
    "suggested_time": "HH:MM" (如果郵件中沒有明確時間，請設為 null),
    "reason": "判斷理由"
}}
"""}
                    ],
                    temperature=0.3
                )
                
                content = response.choices[0].message.content
            
            # 提取JSON
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
                
                if analysis.get('should_add') and analysis.get('confidence', 0) > 0.75:
                    # 如果 LLM 返回 null 或空字符串，嘗試提取時間
                    suggested_time = analysis.get('suggested_time')
                    # 處理 null 字符串
                    if suggested_time == 'null' or not suggested_time:
                        suggested_time = extract_time_from_email(email)
                    
                    suggested_date = analysis.get('suggested_date')
                    # 處理 null 字符串
                    if suggested_date == 'null' or not suggested_date:
                        suggested_date = extract_date_from_email(email)
                    
                    results.append({
                        'email': email,
                        'suggestedDate': suggested_date,
                        'suggestedTime': suggested_time if suggested_time and suggested_time != 'null' else None,
                        'confidence': analysis.get('confidence', 0.8),
                        'source': f"{model_type.upper()} 分析: {analysis.get('reason', '')}"
                    })
                else:
                    # AI 判斷不需要加入或信心不足
                    removed_by_ai.append({
                        'email': email,
                        'reason': analysis.get('reason', 'AI 信心指數不足或判斷不需要加入日曆'),
                        'confidence': analysis.get('confidence', 0)
                    })
                    
        except Exception as e:
            print(f"LLM Analysis Error for email {email['id']}: {e}")
        
        # 每處理完一批郵件後暫停
        if (i + 1) % batch_size == 0 and (i + 1) < len(emails):
            print(f"[DEBUG] 已處理 {i + 1} 封郵件，暫停 {batch_delay} 秒以避免限流...")
            await asyncio.sleep(batch_delay)
            continue
    
    return results, removed_by_ai

@app.post("/api/calendar/batch-add-events")
def batch_add_events(request: BatchAddEventsRequest):
    print(f"Received batch add request with {len(request.events)} events")
    for idx, evt in enumerate(request.events):
        print(f"Event {idx}: title={evt.title}, date={evt.date}, time={evt.time}")
    
    calendar_service = Oauth.get_calendar_service()
    if not calendar_service:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        added_count = 0
        errors = []
        
        for idx, event_req in enumerate(request.events):
            try:
                # 驗證必需字段
                if not event_req.title:
                    errors.append(f"Event {idx}: Missing title")
                    continue
                if not event_req.date:
                    errors.append(f"Event {idx}: Missing date")
                    continue
                
                # 判斷是否為全天事件
                if event_req.isAllDay or not event_req.time:
                    # 全天事件
                    event = {
                        'summary': event_req.title,
                        'description': event_req.description,
                        'start': {
                            'date': event_req.date,
                        },
                        'end': {
                            'date': event_req.date,
                        }
                    }
                else:
                    # 有時間的事件
                    start_datetime = f"{event_req.date}T{event_req.time}:00"
                    
                    # 計算結束時間（+1小時）
                    start_dt = datetime.fromisoformat(start_datetime)
                    end_dt = start_dt + timedelta(hours=1)
                    end_datetime = end_dt.isoformat()
                    
                    event = {
                        'summary': event_req.title,
                        'description': event_req.description,
                        'start': {
                            'dateTime': start_datetime,
                            'timeZone': 'Asia/Taipei',
                        },
                        'end': {
                            'dateTime': end_datetime,
                            'timeZone': 'Asia/Taipei',
                        }
                    }
                
                calendar_service.events().insert(calendarId='primary', body=event).execute()
                added_count += 1
            except Exception as e:
                error_msg = f"Event {idx} ({event_req.title}): {str(e)}"
                print(f"Error adding event: {error_msg}")
                errors.append(error_msg)
        
        if errors and added_count == 0:
            raise HTTPException(status_code=500, detail=f"Failed to add all events. Errors: {'; '.join(errors)}")
        
        return {
            "success": True, 
            "added_count": added_count,
            "errors": errors if errors else None
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Batch Add Events Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
