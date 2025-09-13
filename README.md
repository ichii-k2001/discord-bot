# Multi-Feature Discord Bot (Koyeb Deployment)

## 🎯 概要

- Python製の多機能Discord BotをGitHubにアップロード
- Koyebにデプロイして24時間稼働
- スプラトゥーン、カレンダー、タスク管理機能を搭載
- `.env` はGitHubに含めず、Koyeb Web UIで管理

---

## 📁 プロジェクト構成

```
discord-bot/
├── app/
│   ├── bot.py               # Discord Bot メインロジック
│   ├── cogs/                # 機能別Cogディレクトリ
│   │   ├── splatoon.py      # スプラトゥーン機能
│   │   ├── calendar.py      # カレンダー機能
│   │   ├── tasks.py         # タスク管理機能
│   │   ├── qr.py            # QRコード機能
│   │   └── general.py       # 全般機能
│   └── services/            # サービス層
│       ├── google_calendar.py   # Googleカレンダー連携
│       ├── google_sheets.py     # Googleスプレッドシート連携

├── data/                    # データファイル保存用
│   ├── .gitkeep
│   ├── weapon_to_groups.json    # ブキデータ
│   ├── team_patterns.json       # 編成パターン
│   ├── events.json              # カレンダー予定データ（自動生成）
│   ├── tasks.json               # タスクデータ（自動生成）

├── docs/                    # ドキュメント
│   ├── SETUP.md
│   ├── FEATURES.md
│   ├── GOOGLE_CALENDAR_SETUP.md
│   ├── GOOGLE_SHEETS_SETUP.md

├── server.py                # FastAPI + Bot起動エントリーポイント
├── requirements.txt         # ライブラリ定義
├── Dockerfile               # デプロイ用設定
├── .env                     # ローカル用（Gitには含めない）
├── .env.example             # 共有用テンプレ
└── .gitignore               # 除外ファイル指定
```

---

## ✅ ローカル開発手順

1. `.env` ファイル作成

```
DISCORD_TOKEN=your_discord_token
```

2. 仮想環境を使って依存をインストール

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

3. サーバー起動

```bash
uvicorn server:app --host 0.0.0.0 --port 8080
```

4. 動作確認

- http://localhost:8080/ にアクセス → `{"message": "Bot is running!"}`
- Discordで `/splatoon_help` などのスラッシュコマンドが動作

---

## ✅ GitHubへのアップロード

1. `.env` は `.gitignore` によって除外
2. `.env.example`, `requirements.txt`, `Dockerfile` 等を含めてアップロード

---

## ✅ Koyebへのデプロイ

1. GitHub連携でリポジトリを選択
2. Dockerfile により自動ビルド
3. 環境変数 `DISCORD_TOKEN` を設定
4. ビルド成功後、公開URLが発行される（例：`https://splatoon-bot-xxxx.koyeb.app`）

---

## ✅ UptimeRobotで常時稼働

1. https://uptimerobot.com に登録
2. 「Add New Monitor」で Koyeb URL を5分間隔で監視

---

## ✅ JSONファイル例

### data/weapon_to_groups.json

スプラトゥーンのブキデータを定義するファイル。各ブキにロールとタイプを設定。

```json
{
  "スプラシューター": [
    "role:前衛キル特化ブキ",
    "role:オールラウンダーブキ",
    "type:シューター種"
  ],
  "スプラチャージャー": [
    "role:後衛ブキ",
    "type:チャージャー種"
  ]
}
```

### data/team_patterns.json

チーム編成パターンを定義するファイル。

```json
{
  "default": [
    "role:前衛キル特化ブキ",
    "role:前衛キル特化ブキ",
    "role:オールラウンダーブキ",
    "role:後衛ブキ"
  ],
  "no_backline": [
    "role:前衛キル特化ブキ",
    "role:前衛キル特化ブキ",
    "role:オールラウンダーブキ",
    "role:オールラウンダーブキ"
  ]
}
```

---

## ✅ 利用可能な機能

### 🎮 スプラトゥーン機能
- `/splatoon_help` - スプラトゥーン機能のヘルプ
- `/splatoon_team [pattern]` - チーム編成
- `/splatoon_weapon <武器名>` - ブキ情報検索
- `/splatoon_role <ロール名>` - ロール別ブキ一覧
- `/splatoon_pattern [パターン名]` - 編成パターン確認

### 📅 カレンダー機能 ⚠️ 実装予定
Google Calendar連携の設定完了後に以下の機能が利用可能になります：
- 予定の追加・編集・削除
- 予定一覧表示・今日の予定確認
- Googleカレンダーとの自動同期
- 期限通知機能

### 📋 タスク管理機能 ⚠️ 実装予定
Google Sheets連携の設定完了後に以下の機能が利用可能になります：
- タスクの追加・完了・削除
- 優先度設定・期限管理
- Googleスプレッドシートとの自動同期
- 期限切れ警告機能

### 📱 QRコード機能
- `/qr_help` - QRコード機能のヘルプ
- `/qr <テキスト>` - QRコード生成（URL、テキストなど）

### 🤖 全般機能
- `/help` - 全体のコマンド一覧
- `/ping` - Bot応答確認


---

## ✅ トラブルシュート

### 基本的な問題
| 症状 | 対策 |
|------|------|
| `KeyError: DISCORD_TOKEN` | Koyeb で環境変数が未設定 |
| Bot がスリープする | UptimeRobot で監視追加 |
| コマンドが補完されない | `/help` で確認、同期に時間がかかることも |

### Google 連携の問題
| 症状 | 対策 |
|------|------|
| カレンダー連携エラー | `/calendar_sync` で状態確認、認証情報を再確認 |
| スプレッドシート連携エラー | `/task_sync` で状態確認、スプレッドシート ID を確認 |
| 認証エラー | `credentials.json` の配置と内容を確認 |


---

## 📚 ドキュメント

### 🚀 セットアップ・基本操作
- [セットアップガイド](docs/SETUP.md) - 詳細なセットアップ手順
- [機能詳細ガイド](docs/FEATURES.md) - 各機能の詳細説明

### 🔗 Google連携
- [Googleカレンダー連携](docs/GOOGLE_CALENDAR_SETUP.md) - Googleカレンダー連携の設定方法
- [Googleスプレッドシート連携](docs/GOOGLE_SHEETS_SETUP.md) - Googleスプレッドシート連携の設定方法


### 📝 その他
- [変更履歴](docs/CHANGELOG.md) - バージョン別の変更内容

## 🧩 技術的特徴

### 🏗️ アーキテクチャ
- **FastAPI**: Web サーバーとして使用、将来的な API 拡張に対応
- **Cog ベース**: 機能別に分離された拡張可能な構成
- **サービス層**: Google 連携やユーザー設定を独立したサービスとして管理
- **ハイブリッド データ管理**: ローカル JSON ファイルと Google サービスの自動切り替え

### 🔄 データ管理
- **ローカル**: JSON ファイルでの軽量データ管理
- **Google 連携**: カレンダーとスプレッドシートでのクラウド同期


## 🔧 新機能の追加方法

1. `app/cogs/` ディレクトリに新しいCogファイルを作成
2. `app/bot.py` の `setup_hook` メソッドで新しいCogを読み込み
3. 必要に応じて `requirements.txt` に依存関係を追加

## 📊 データファイルについて

### 自動生成されるファイル
- `data/events.json` - カレンダー予定データ（ローカルモード時）
- `data/tasks.json` - タスク管理データ（ローカルモード時）

- `data/token.json` - Google Calendar API トークン（認証後）
- `data/sheets_token.json` - Google Sheets API トークン（認証後）

これらのファイルは初回実行時に自動生成されます。

### 手動編集が必要なファイル
- `data/weapon_to_groups.json` - スプラトゥーンのブキデータ
- `data/team_patterns.json` - チーム編成パターン

### 認証情報ファイル（手動配置）
- `credentials.json` - Google API 認証情報（プロジェクトルートに配置）

## 🔄 機能の有効/無効切り替え

### Cog レベルでの制御
特定の機能を無効にしたい場合は、`app/bot.py` の `setup_hook` メソッドで該当する `load_extension` をコメントアウトしてください。

```python
async def setup_hook(self):
    await self.load_extension("app.cogs.splatoon")
    await self.load_extension("app.cogs.calendar")
    await self.load_extension("app.cogs.tasks")

    # await self.load_extension("app.cogs.general")  # 無効化例
```

### Google 連携の制御
環境変数の設定により、Google 連携機能の有効/無効を制御できます：

```env
# Googleカレンダー連携を無効にする場合
# GOOGLE_CREDENTIALS_PATH=credentials.json  # コメントアウト

# Googleスプレッドシート連携を無効にする場合
# GOOGLE_SPREADSHEET_ID=your_spreadsheet_id  # コメントアウト
```

## 🌐 Google連携機能

### 📅 Googleカレンダー連携
- Discord上で追加した予定がGoogleカレンダーに自動同期
- Googleカレンダーの予定をDiscordで表示

### 📊 Googleスプレッドシート連携
- Discord上で追加したタスクがGoogleスプレッドシートに自動同期
- スプレッドシート上でのタスク管理・チーム共有

## 🚀 将来の拡張予定

### 📊 データ管理
- **データベース連携**: SQLite や PostgreSQL での永続化
- **データ同期**: 複数サーバー間でのデータ共有
- **バックアップ機能**: 自動データバックアップ

### 🔔 通知・自動化
- **期限通知**: タスクやイベントの自動リマインダー
- **定期実行**: 日次・週次レポートの自動生成
- **Webhook 連携**: 外部サービスとの連携

### 🌐 インターフェース
- **Web UI**: ブラウザからの管理画面
- **モバイル対応**: スマートフォン向け最適化
- **API 拡張**: REST API での外部連携

### 🌍 多言語・アクセシビリティ
- **多言語対応**: 英語やその他言語のサポート
- **タイムゾーン対応**: 地域別時刻表示
- **アクセシビリティ**: 視覚障害者向け対応