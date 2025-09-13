# 機能詳細ガイド

## 🎮 スプラトゥーン機能

### 概要
スプラトゥーンのブキを使ったチーム編成やブキ情報検索機能を提供します。

### コマンド一覧

#### `/splatoon_team [pattern]`
- **説明**: ランダムなブキでチーム編成を行います
- **パラメータ**: 
  - `pattern` (省略可): 編成パターン名（デフォルト: "default"）
- **使用例**: 
  - `/splatoon_team` - デフォルト編成
  - `/splatoon_team no_backline` - 後衛なし編成

#### `/splatoon_weapon <ブキ名>`
- **説明**: 指定したブキの詳細情報を表示
- **パラメータ**: 
  - `weapon_name`: 調べたいブキ名（オートコンプリート対応）
- **使用例**: `/splatoon_weapon スプラシューター`

#### `/splatoon_role <ロール名>`
- **説明**: 指定したロールに属するブキ一覧を表示
- **パラメータ**: 
  - `role_name`: ロール名（オートコンプリート対応）
- **使用例**: `/splatoon_role 前衛キル特化ブキ`

#### `/splatoon_pattern [パターン名]`
- **説明**: 編成パターンの確認
- **パラメータ**: 
  - `pattern` (省略可): パターン名
- **使用例**: 
  - `/splatoon_pattern` - 全パターン一覧
  - `/splatoon_pattern default` - 特定パターンの詳細

### カスタマイズ

`data/weapon_to_groups.json` でブキデータを編集可能：

```json
{
  "ブキ名": [
    "role:ロール名",
    "type:タイプ名"
  ]
}
```

利用可能なロール：
- `前衛キル特化ブキ`
- `オールラウンダーブキ`
- `後衛ブキ`
- `サポート特化ブキ`
- `塗り特化ブキ`
- `ヘイト特化ブキ`

---

## 📅 カレンダー機能 ⚠️ 実装予定

### 概要
予定の追加、表示、管理機能を提供します。現在Google Calendar連携の設定作業中のため、一時的に無効化されています。

### 実装予定のコマンド一覧

Google Calendar連携設定完了後に利用可能になります。

#### `/calendar_add <タイトル> <日付> [時刻] [説明]`
- **説明**: 新しい予定を追加
- **パラメータ**: 
  - `title`: 予定のタイトル（必須）
  - `date`: 日付（YYYY-MM-DD形式、必須）
  - `time`: 時刻（HH:MM形式、省略可）
  - `description`: 詳細説明（省略可）
- **使用例**: 
  - `/calendar_add 会議 2025-01-15`
  - `/calendar_add 会議 2025-01-15 14:30 プロジェクト進捗確認`

#### `/calendar_list [日数]`
- **説明**: 予定一覧を表示
- **パラメータ**: 
  - `days`: 表示する日数（デフォルト: 7日）
- **使用例**: 
  - `/calendar_list` - 7日間の予定
  - `/calendar_list 14` - 14日間の予定

#### `/calendar_today`
- **説明**: 今日の予定を表示
- **使用例**: `/calendar_today`

#### `/calendar_delete <予定ID>`
- **説明**: 予定を削除
- **パラメータ**: 
  - `event_id`: 削除する予定のID
- **使用例**: `/calendar_delete 1`

### データ形式

**ローカルモード時**: 予定データは `data/events.json` に保存されます：

```json
[
  {
    "id": 1,
    "title": "会議",
    "date": "2025-01-15",
    "time": "14:30",
    "description": "プロジェクト進捗確認",
    "created_by": "123456789",
    "created_at": "2025-01-10T10:00:00",
    "google_event_id": "abc123",
    "html_link": "https://calendar.google.com/..."
  }
]
```

**Google連携時**: Googleカレンダーに直接保存され、上記形式で取得されます。

---

## 📋 タスク管理機能 ⚠️ 実装予定

### 概要
タスクの追加、管理、期限確認機能を提供します。現在Google Sheets連携の設定作業中のため、一時的に無効化されています。

### 実装予定のコマンド一覧

Google Sheets連携設定完了後に利用可能になります。

#### `/task_add <タイトル> [期限] [優先度] [説明]`
- **説明**: 新しいタスクを追加
- **パラメータ**: 
  - `title`: タスクのタイトル（必須）
  - `due_date`: 期限（YYYY-MM-DD形式、省略可）
  - `priority`: 優先度（high/medium/low、デフォルト: medium）
  - `description`: 詳細説明（省略可）
- **使用例**: 
  - `/task_add レポート作成`
  - `/task_add レポート作成 2025-01-20 high 月次売上レポート`

#### `/task_list [状態] [優先度]`
- **説明**: タスク一覧を表示
- **パラメータ**: 
  - `status`: 状態（all/pending/completed、デフォルト: pending）
  - `priority`: 優先度（all/high/medium/low、デフォルト: all）
- **使用例**: 
  - `/task_list` - 未完了タスク一覧
  - `/task_list completed` - 完了済みタスク一覧
  - `/task_list pending high` - 未完了の高優先度タスク

#### `/task_complete <タスクID>`
- **説明**: タスクを完了にする
- **パラメータ**: 
  - `task_id`: 完了するタスクのID
- **使用例**: `/task_complete 1`

#### `/task_delete <タスクID>`
- **説明**: タスクを削除
- **パラメータ**: 
  - `task_id`: 削除するタスクのID
- **使用例**: `/task_delete 1`

#### `/task_due [日数]`
- **説明**: 期限が近いタスクを表示
- **パラメータ**: 
  - `days`: 何日以内の期限を表示するか（デフォルト: 3日）
- **使用例**: 
  - `/task_due` - 3日以内の期限
  - `/task_due 7` - 7日以内の期限

### 優先度と表示

- 🔴 **高優先度** (high)
- 🟡 **中優先度** (medium)
- 🟢 **低優先度** (low)

### データ形式

**ローカルモード時**: タスクデータは `data/tasks.json` に保存されます：

```json
[
  {
    "id": 1,
    "title": "レポート作成",
    "description": "月次売上レポート",
    "due_date": "2025-01-20",
    "priority": "high",
    "status": "pending",
    "created_by": "123456789",
    "created_at": "2025-01-10T10:00:00",
    "completed_at": null
  }
]
```

**Google連携時**: Googleスプレッドシートに保存され、以下の列構成になります：

| ID | タイトル | 説明 | 期限 | 優先度 | ステータス | 作成者 | 作成日時 | 完了日時 |
|----|----------|------|------|--------|------------|--------|----------|----------|

---

## 📱 QRコード機能

### 概要
テキストやURLを高品質なQRコードに変換する機能を提供します。

### コマンド一覧

#### `/qr <テキスト>`
テキストやURLをQRコードに変換します。

**パラメータ:**
- `text`: QRコードに変換するテキストまたはURL（必須）

**使用例:**
```bash
# URLをQRコードに変換
/qr https://example.com

# テキストをQRコードに変換
/qr Hello World!

# 長いテキストも対応
/qr WiFiパスワード: MySecurePassword123
```

**機能:**
- 任意のテキストやURLをQRコードに変換
- 生成されたQRコードは画像として表示
- 長いテキストは自動的に省略表示
- エラーハンドリング付き
- 生成者情報と生成時刻を記録

#### `/qr_help`
QRコード機能の詳細なヘルプを表示します。

**使用例:** `/qr_help`

---

## 🤖 全般機能

### `/help`
全機能のコマンド一覧を表示

### `/ping`
Botの応答速度を確認

---



## 🔧 カスタマイズ

### 新機能の追加

1. `app/cogs/` に新しいCogファイルを作成
2. `app/bot.py` で新しいCogを読み込み
3. 必要に応じて `requirements.txt` に依存関係を追加
4. Google連携が必要な場合は `app/services/` にサービスクラスを作成

### 既存機能の修正

各Cogファイルを直接編集することで機能をカスタマイズできます。

### データファイルの場所

**設定ファイル:**
- スプラトゥーンデータ: `data/weapon_to_groups.json`, `data/team_patterns.json`


**ローカルデータ:**
- カレンダーデータ: `data/events.json` (自動生成、ローカルモード時)
- タスクデータ: `data/tasks.json` (自動生成、ローカルモード時)

**認証情報:**
- Google認証: `credentials.json` (手動配置)
- APIトークン: `data/token.json`, `data/sheets_token.json` (自動生成)