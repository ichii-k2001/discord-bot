import os
from datetime import datetime
from typing import Optional, List, Dict
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class GoogleSheetsService:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        self.credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
        self.token_path = 'data/sheets_token.json'
        self.spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
        self.sheet_name = os.getenv('GOOGLE_SHEET_NAME', 'Tasks')
        self.service = None
        
        # スプレッドシートのヘッダー
        self.headers = [
            'ID', 'タイトル', '説明', '期限', '優先度', 
            'ステータス', '作成者', '作成日時', '完了日時'
        ]

    def authenticate(self) -> bool:
        """Google Sheets APIの認証を行う"""
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
            self.service = build('sheets', 'v4', credentials=creds)
            return True
        except Exception as e:
            print(f"Google Sheets サービスの初期化に失敗: {e}")
            return False

    def initialize_sheet(self) -> bool:
        """スプレッドシートを初期化（ヘッダー行を作成）"""
        if not self.service:
            if not self.authenticate():
                return False
        
        try:
            # ヘッダー行が存在するかチェック
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f'{self.sheet_name}!A1:I1'
            ).execute()
            
            values = result.get('values', [])
            
            # ヘッダー行が存在しない場合は作成
            if not values or values[0] != self.headers:
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=f'{self.sheet_name}!A1:I1',
                    valueInputOption='RAW',
                    body={'values': [self.headers]}
                ).execute()
                print("スプレッドシートのヘッダー行を初期化しました")
            
            return True
            
        except HttpError as e:
            print(f"Google Sheets APIエラー: {e}")
            return False
        except Exception as e:
            print(f"スプレッドシート初期化エラー: {e}")
            return False

    def add_task(self, title: str, due_date: Optional[str] = None, 
                priority: str = "medium", description: Optional[str] = None,
                created_by: str = "") -> Optional[int]:
        """タスクをスプレッドシートに追加"""
        if not self.service:
            if not self.authenticate():
                return None
        
        if not self.initialize_sheet():
            return None
        
        try:
            # 次のIDを取得
            task_id = self._get_next_id()
            
            # タスクデータを準備
            task_data = [
                task_id,
                title,
                description or "",
                due_date or "",
                priority,
                "pending",
                created_by,
                datetime.now().isoformat(),
                ""  # 完了日時は空
            ]
            
            # スプレッドシートに追加
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f'{self.sheet_name}!A:I',
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body={'values': [task_data]}
            ).execute()
            
            return task_id
            
        except HttpError as e:
            print(f"Google Sheets APIエラー: {e}")
            return None
        except Exception as e:
            print(f"タスク追加エラー: {e}")
            return None

    def get_tasks(self, status: str = "all", priority: str = "all") -> List[Dict]:
        """スプレッドシートからタスクを取得"""
        if not self.service:
            if not self.authenticate():
                return []
        
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f'{self.sheet_name}!A:I'
            ).execute()
            
            values = result.get('values', [])
            
            if not values or len(values) < 2:  # ヘッダー行のみの場合
                return []
            
            tasks = []
            for row in values[1:]:  # ヘッダー行をスキップ
                if len(row) < 9:
                    row.extend([''] * (9 - len(row)))  # 不足している列を空文字で埋める
                
                task = {
                    'id': int(row[0]) if row[0] else 0,
                    'title': row[1],
                    'description': row[2],
                    'due_date': row[3] if row[3] else None,
                    'priority': row[4],
                    'status': row[5],
                    'created_by': row[6],
                    'created_at': row[7],
                    'completed_at': row[8] if row[8] else None
                }
                
                # フィルタリング
                if status != "all" and task['status'] != status:
                    continue
                if priority != "all" and task['priority'] != priority:
                    continue
                
                tasks.append(task)
            
            return tasks
            
        except HttpError as e:
            print(f"Google Sheets APIエラー: {e}")
            return []
        except Exception as e:
            print(f"タスク取得エラー: {e}")
            return []

    def update_task_status(self, task_id: int, status: str) -> bool:
        """タスクのステータスを更新"""
        if not self.service:
            if not self.authenticate():
                return False
        
        try:
            # タスクの行を見つける
            row_index = self._find_task_row(task_id)
            if row_index == -1:
                return False
            
            # ステータスを更新
            status_range = f'{self.sheet_name}!F{row_index}'
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=status_range,
                valueInputOption='RAW',
                body={'values': [[status]]}
            ).execute()
            
            # 完了日時を更新（完了の場合）
            if status == "completed":
                completed_range = f'{self.sheet_name}!I{row_index}'
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=completed_range,
                    valueInputOption='RAW',
                    body={'values': [[datetime.now().isoformat()]]}
                ).execute()
            
            return True
            
        except HttpError as e:
            print(f"Google Sheets APIエラー: {e}")
            return False
        except Exception as e:
            print(f"タスク更新エラー: {e}")
            return False

    def delete_task(self, task_id: int) -> bool:
        """タスクを削除"""
        if not self.service:
            if not self.authenticate():
                return False
        
        try:
            # タスクの行を見つける
            row_index = self._find_task_row(task_id)
            if row_index == -1:
                return False
            
            # 行を削除
            request = {
                'deleteDimension': {
                    'range': {
                        'sheetId': 0,  # 最初のシートのID
                        'dimension': 'ROWS',
                        'startIndex': row_index - 1,  # 0ベースのインデックス
                        'endIndex': row_index
                    }
                }
            }
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={'requests': [request]}
            ).execute()
            
            return True
            
        except HttpError as e:
            print(f"Google Sheets APIエラー: {e}")
            return False
        except Exception as e:
            print(f"タスク削除エラー: {e}")
            return False

    def _get_next_id(self) -> int:
        """次のタスクIDを取得"""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f'{self.sheet_name}!A:A'
            ).execute()
            
            values = result.get('values', [])
            
            if len(values) <= 1:  # ヘッダー行のみ
                return 1
            
            # 最大IDを見つける
            max_id = 0
            for row in values[1:]:
                if row and row[0]:
                    try:
                        task_id = int(row[0])
                        max_id = max(max_id, task_id)
                    except ValueError:
                        continue
            
            return max_id + 1
            
        except Exception as e:
            print(f"ID取得エラー: {e}")
            return 1

    def _find_task_row(self, task_id: int) -> int:
        """タスクIDから行番号を取得"""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f'{self.sheet_name}!A:A'
            ).execute()
            
            values = result.get('values', [])
            
            for i, row in enumerate(values[1:], start=2):  # ヘッダー行をスキップ、行番号は2から
                if row and row[0] and int(row[0]) == task_id:
                    return i
            
            return -1
            
        except Exception as e:
            print(f"行検索エラー: {e}")
            return -1

    def is_available(self) -> bool:
        """Google Sheets連携が利用可能かチェック"""
        return (
            os.path.exists(self.credentials_path) and 
            os.getenv('GOOGLE_CREDENTIALS_PATH') is not None and
            os.getenv('GOOGLE_SPREADSHEET_ID') is not None
        )

    def get_sheet_url(self) -> str:
        """スプレッドシートのURLを取得"""
        if self.spreadsheet_id:
            return f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/edit"
        return ""