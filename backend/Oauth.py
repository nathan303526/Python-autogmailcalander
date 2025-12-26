from __future__ import print_function
import os.path
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar.events'
]

TOKEN_FILE = 'token.json'
CREDENTIALS_FILE = 'credentials.json'

def get_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # 如果 token 過期，嘗試刷新
    if creds and creds.expired and creds.refresh_token:
        try:
            print("[DEBUG] Token 已過期，正在刷新...")
            creds.refresh(Request())
            # 保存刷新後的 token
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
            print("[DEBUG] Token 刷新成功")
        except Exception as e:
            print(f"[ERROR] Token 刷新失敗: {e}")
            return None
    
    return creds

def get_gmail_service():
    creds = get_credentials()
    if creds and creds.valid:
        return build('gmail', 'v1', credentials=creds)
    return None

def get_calendar_service():
    creds = get_credentials()
    if creds and creds.valid:
        return build('calendar', 'v3', credentials=creds)
    return None

