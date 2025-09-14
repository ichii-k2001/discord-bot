import os
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class GoogleCalendarService:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/calendar']
        self.credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
        self.token_path = 'data/token.json'
        self.calendar_id = os.getenv('GOOGLE_CALENDAR_ID', 'primary')
        self.service = None

    def authenticate(self) -> bool:
        """Google Calendar APIの認証を行う"""
        creds = None
        
        # 既存のトークンファイルをチェック
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)
        
        # 認証情報が無効または存在しない場合
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"トークンの更新に失敗: {e}")
                    return False
            else:
                # 認証情報ファイルが存在しない場合
                if not os.path.exists(self.credentials_path):
                    print(f"認証情報ファイルが見つかりません: {self.credentials_path}")
                    return False
                
                try:
                    flow = Flow.from_client_secrets_file(self.credentials_path, self.SCOPES)
                    flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
                    
                    auth_url, _ = flow.authorization_url(prompt='consent')
                    print(f"以下のURLにアクセスして認証してください:\n{auth_url}")
                    
                    code = input('認証コードを入力してください: ')
                    flow.fetch_token(code=code)
                    creds = flow.credentials
                except Exception as e:
                    print(f"認証に失敗: {e}")
                    return False
            
            # トークンを保存
            os.makedirs(os.path.dirname(self.token_path), exist_ok=True)
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
        
        try:
            self.service = build('calendar', 'v3', credentials=creds)
            return True
        except Exception as e:
            print(f"Google Calendar サービスの初期化に失敗: {e}")
            return False

    def create_event(self, title: str, date: str, time: Optional[str] = None, 
                    description: Optional[str] = None) -> Optional[Dict]:
        """Googleカレンダーにイベントを作成"""
        if not self.service:
            if not self.authenticate():
                return None
        
        try:
            # 日時の設定
            start_datetime = datetime.strptime(date, "%Y-%m-%d")
            if time:
                time_obj = datetime.strptime(time, "%H:%M").time()
                start_datetime = datetime.combine(start_datetime.date(), time_obj)
                end_datetime = start_datetime + timedelta(hours=1)  # デフォルト1時間
                
                event_body = {
                    'summary': title,
                    'description': description or '',
                    'start': {
                        'dateTime': start_datetime.isoformat(),
                        'timeZone': 'Asia/Tokyo',
                    },
                    'end': {
                        'dateTime': end_datetime.isoformat(),
                        'timeZone': 'Asia/Tokyo',
                    },
                }
            else:
                # 終日イベント
                event_body = {
                    'summary': title,
                    'description': description or '',
                    'start': {
                        'date': date,
                    },
                    'end': {
                        'date': date,
                    },
                }
            
            event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event_body
            ).execute()
            
            return {
                'id': event['id'],
                'title': event['summary'],
                'date': date,
                'time': time,
                'description': description,
                'google_event_id': event['id'],
                'html_link': event.get('htmlLink', '')
            }
            
        except HttpError as e:
            print(f"Google Calendar APIエラー: {e}")
            return None
        except Exception as e:
            print(f"イベント作成エラー: {e}")
            return None

    def get_events(self, days: int = 7) -> List[Dict]:
        """Googleカレンダーからイベントを取得"""
        if not self.service:
            if not self.authenticate():
                return []
        
        try:
            now = datetime.now()
            end_time = now + timedelta(days=days)
            
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=now.isoformat() + 'Z',
                timeMax=end_time.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            formatted_events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                
                # 日付と時刻の解析
                if 'T' in start:  # 時刻付きイベント
                    dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    date_str = dt.strftime('%Y-%m-%d')
                    time_str = dt.strftime('%H:%M')
                else:  # 終日イベント
                    date_str = start
                    time_str = None
                
                formatted_events.append({
                    'id': event['id'],
                    'title': event.get('summary', '無題'),
                    'date': date_str,
                    'time': time_str,
                    'description': event.get('description', ''),
                    'google_event_id': event['id'],
                    'html_link': event.get('htmlLink', '')
                })
            
            return formatted_events
            
        except HttpError as e:
            print(f"Google Calendar APIエラー: {e}")
            return []
        except Exception as e:
            print(f"イベント取得エラー: {e}")
            return []

    def delete_event(self, event_id: str) -> bool:
        """Googleカレンダーからイベントを削除"""
        if not self.service:
            if not self.authenticate():
                return False
        
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            return True
            
        except HttpError as e:
            print(f"Google Calendar APIエラー: {e}")
            return False
        except Exception as e:
            print(f"イベント削除エラー: {e}")
            return False

    def is_available(self) -> bool:
        """Google Calendar連携が利用可能かチェック"""
        return (
            os.path.exists(self.credentials_path) and 
            os.getenv('GOOGLE_CREDENTIALS_PATH') is not None
        )