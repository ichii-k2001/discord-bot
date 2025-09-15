# システムアーキテクチャ

## 🎯 概要

Discord Botは多機能なサーバーサイドアプリケーションとして設計されており、翻訳、スプラトゥーン、QRコード、リマインダー、カレンダー、タスク管理機能を提供します。

## 🏗️ システム全体アーキテクチャ

```mermaid
graph TB
    subgraph "Discord Platform"
        DC[Discord Client]
        DS[Discord Server]
    end
    
    subgraph "Koyeb Cloud Platform"
        subgraph "Discord Bot Application"
            FB[FastAPI Server :8080]
            BOT[Discord Bot Core]
            
            subgraph "Cogs Layer"
                TC[Translate Cog]
                SC[Splatoon Cog]
                QC[QR Cog]
                RC[Reminder Cog]
                CC[Calendar Cog]
                TKC[Task Cog]
                GC[General Cog]
            end
            
            subgraph "Service Layer"
                TS[Translate Service]
                GCS[Google Calendar Service]
                GSS[Google Sheets Service]
            end
            
            subgraph "Data Layer"
                JSON[(JSON Files)]
                CACHE[Memory Cache]
            end
        end
    end
    
    subgraph "External Services"
        GT[Google Translate API]
        GCA[Google Calendar API]
        GSA[Google Sheets API]
    end
    
    subgraph "Monitoring"
        UR[UptimeRobot]
        GH[GitHub Repository]
    end
    
    %% User Interactions
    DC --> DS
    DS --> BOT
    
    %% Bot Internal Flow
    BOT --> TC
    BOT --> SC
    BOT --> QC
    BOT --> RC
    BOT --> CC
    BOT --> TKC
    BOT --> GC
    
    %% Service Layer Connections
    TC --> TS
    CC --> GCS
    TKC --> GSS
    
    %% Data Connections
    SC --> JSON
    RC --> JSON
    CC --> JSON
    TKC --> JSON
    TS --> CACHE
    
    %% External API Connections
    TS --> GT
    GCS --> GCA
    GSS --> GSA
    
    %% Infrastructure
    FB --> BOT
    UR --> FB
    GH --> Koyeb
    
    %% Styling
    classDef cogClass fill:#e1f5fe
    classDef serviceClass fill:#f3e5f5
    classDef dataClass fill:#e8f5e8
    classDef externalClass fill:#fff3e0
    
    class TC,SC,QC,RC,CC,TKC,GC cogClass
    class TS,GCS,GSS serviceClass
    class JSON,CACHE dataClass
    class GT,GCA,GSA,UR,GH externalClass
```

## 🔧 コンポーネント構成

### 1. **プレゼンテーション層（Cogs）**

```mermaid
classDiagram
    class BaseCog {
        +bot: Bot
        +__init__(bot)
        +setup()
    }
    
    class TranslateCog {
        +translate_service: TranslateService
        +translate(language, text, show_details)
        +translate_help()
        +language_choices: List[Choice]
    }
    
    class SplatoonCog {
        +formation(pattern)
        +lookup_weapon(weapon_name)
        +list_by_role(role_name)
        +show_pattern(pattern)
    }
    
    class ReminderCog {
        +reminder_manager: ReminderManager
        +remind(time, message)
        +remind_at(date, time, message)
        +remind_list()
        +check_reminders()
    }
    
    class QRCog {
        +generate_qr(text)
        +qr_help()
    }
    
    class CalendarCog {
        +google_calendar: GoogleCalendarService
        +add_event(title, date, time)
        +list_events(days)
        +sync_status()
    }
    
    class TaskCog {
        +google_sheets: GoogleSheetsService
        +add_task(title, due_date, priority)
        +complete_task(task_id)
        +list_tasks(status, priority)
    }
    
    BaseCog <|-- TranslateCog
    BaseCog <|-- SplatoonCog
    BaseCog <|-- ReminderCog
    BaseCog <|-- QRCog
    BaseCog <|-- CalendarCog
    BaseCog <|-- TaskCog
```

### 2. **サービス層**

```mermaid
classDiagram
    class TranslateService {
        +translator: Translator
        +cache: Dict
        +user_usage: Dict
        +LANGUAGES: Dict[ja,en,zh-cn,zh-tw,ko,fr,de,es]
        +translate_text(text, target_lang, user_id)
        +check_rate_limit(user_id)
        +get_cached_translation(text, target_lang)
        +get_language_choices()
    }
    
    class GoogleCalendarService {
        +calendar_id: str
        +credentials_path: str
        +authenticate()
        +create_event(title, date, time, description)
        +get_events(days)
        +is_available()
    }
    
    class GoogleSheetsService {
        +spreadsheet_id: str
        +sheet_name: str
        +credentials_path: str
        +authenticate()
        +add_task(title, due_date, priority, description)
        +get_tasks(status, priority)
        +update_task_status(task_id, status)
    }
    
    class ReminderManager {
        +file_path: str
        +load_reminders()
        +save_reminders(reminders)
        +add_reminder(user_id, channel_id, message, target_time)
        +get_due_reminders()
        +remove_reminder(reminder_id)
    }
```

## 📊 データフロー図

### 翻訳機能のデータフロー

```mermaid
flowchart TD
    A[ユーザー入力] --> B{レート制限チェック}
    B -->|制限内| C{キャッシュ確認}
    B -->|制限超過| D[エラー応答]
    C -->|キャッシュヒット| E[キャッシュから取得]
    C -->|キャッシュミス| F[Google Translate API]
    F --> G[翻訳結果]
    G --> H[キャッシュに保存]
    H --> I[使用統計更新]
    E --> I
    I --> J[Discord応答]
    
    style A fill:#e3f2fd
    style D fill:#ffebee
    style J fill:#e8f5e8
```

### リマインダー機能のデータフロー

```mermaid
flowchart TD
    A[リマインダー設定] --> B[時間解析]
    B --> C{有効な時間?}
    C -->|Yes| D[JSON保存]
    C -->|No| E[エラー応答]
    D --> F[設定完了応答]
    
    G[バックグラウンドタスク] --> H[JSON読み込み]
    H --> I{期限チェック}
    I -->|期限到達| J[Discord通知]
    I -->|未到達| K[待機]
    J --> L[リマインダー削除]
    
    style A fill:#e3f2fd
    style E fill:#ffebee
    style F fill:#e8f5e8
    style J fill:#fff3e0
```

## 🚀 デプロイメント構成

```mermaid
graph TB
    subgraph "Development"
        DEV[Local Development]
        GIT[Git Repository]
    end
    
    subgraph "GitHub"
        REPO[GitHub Repository]
        ACTIONS[GitHub Actions]
    end
    
    subgraph "Koyeb Platform"
        BUILD[Build Process]
        DEPLOY[Deployment]
        APP[Running Application]
        
        subgraph "Application Runtime"
            FASTAPI[FastAPI Server :8080]
            DISCORD[Discord Bot]
            COGS[Loaded Cogs]
        end
    end
    
    subgraph "External Monitoring"
        UPTIME[UptimeRobot]
        HEALTH[Health Checks]
    end
    
    subgraph "External APIs"
        GOOGLE[Google APIs]
        DISCORD_API[Discord API]
    end
    
    %% Development Flow
    DEV --> GIT
    GIT --> REPO
    
    %% Deployment Flow
    REPO --> BUILD
    BUILD --> DEPLOY
    DEPLOY --> APP
    
    %% Runtime Connections
    APP --> FASTAPI
    APP --> DISCORD
    DISCORD --> COGS
    
    %% External Connections
    UPTIME --> FASTAPI
    HEALTH --> FASTAPI
    COGS --> GOOGLE
    DISCORD --> DISCORD_API
    
    %% Styling
    classDef devClass fill:#e3f2fd
    classDef deployClass fill:#f3e5f5
    classDef runtimeClass fill:#e8f5e8
    classDef externalClass fill:#fff3e0
    
    class DEV,GIT devClass
    class REPO,ACTIONS,BUILD,DEPLOY deployClass
    class APP,FASTAPI,DISCORD,COGS runtimeClass
    class UPTIME,HEALTH,GOOGLE,DISCORD_API externalClass
```

## 🔄 技術スタック

### **フロントエンド**
- **Discord Client**: ユーザーインターフェース
- **Discord Slash Commands**: コマンド入力システム

### **バックエンド**
- **Python 3.11+**: メインプログラミング言語
- **discord.py 2.3.2+**: Discord API ライブラリ
- **FastAPI**: Web サーバーフレームワーク
- **uvicorn**: ASGI サーバー

### **外部サービス**
- **Google Translate API**: 翻訳機能
- **Google Calendar API**: カレンダー連携
- **Google Sheets API**: タスク管理連携

### **データストレージ**
- **JSON Files**: ローカルデータ永続化
- **Memory Cache**: 翻訳結果キャッシュ
- **Google Services**: クラウドデータ同期

### **インフラストラクチャ**
- **Koyeb**: クラウドホスティング
- **GitHub**: ソースコード管理
- **UptimeRobot**: 監視・ヘルスチェック

## 🛡️ セキュリティ・制限

### **レート制限**
- 翻訳機能: ユーザー毎に1分3回、1時間20回、1日50回
- リマインダー: 最大30日間設定可能
- QRコード: 特別な制限なし

### **データ保護**
- 環境変数による機密情報管理
- Google API認証情報の安全な保存
- ユーザーデータの最小限収集

### **エラーハンドリング**
- 各機能での包括的例外処理
- ユーザーフレンドリーなエラーメッセージ
- ログ記録とデバッグ情報

## 📈 スケーラビリティ

### **現在の制限**
- 単一インスタンス実行
- メモリベースキャッシュ
- ローカルJSONファイル

### **将来の拡張**
- データベース連携（PostgreSQL/MongoDB）
- Redis キャッシュ
- マルチインスタンス対応
- 負荷分散

## 🔧 設定管理

### **環境変数**
```bash
# 必須
DISCORD_TOKEN=your_discord_token

# Google連携（オプション）
GOOGLE_CREDENTIALS_PATH=credentials.json
GOOGLE_CALENDAR_ID=primary
GOOGLE_SPREADSHEET_ID=your_spreadsheet_id
GOOGLE_SHEET_NAME=Tasks

# 翻訳機能設定（オプション）
TRANSLATE_CACHE_SIZE=1000
TRANSLATE_MAX_TEXT_LENGTH=300
```

### **設定ファイル**
- `data/weapon_to_groups.json`: スプラトゥーンブキデータ
- `data/team_patterns.json`: チーム編成パターン
- `data/reminders.json`: リマインダーデータ（自動生成）
- `data/events.json`: カレンダーデータ（自動生成）
- `data/tasks.json`: タスクデータ（自動生成）

## 🚀 パフォーマンス特性

### **応答時間**
- 一般コマンド: < 100ms
- 翻訳機能: 1-3秒（キャッシュ時 < 100ms）
- QRコード生成: < 500ms
- Google API連携: 1-5秒

### **メモリ使用量**
- ベースBot: ~50MB
- 翻訳キャッシュ: ~10MB（1000エントリ）
- JSONデータ: < 1MB

### **同時処理**
- 非同期処理による高い応答性
- 翻訳API呼び出しの並列実行
- バックグラウンドタスクの独立実行