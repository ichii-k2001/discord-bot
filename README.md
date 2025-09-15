# Multi-Feature Discord Bot (Koyeb Deployment)

## 🎯 概要

- Python製の多機能Discord BotをGitHubにアップロード
- Koyebにデプロイして24時間稼働
- スプラトゥーン、翻訳、QRコード、リマインダー機能を搭載
- カレンダー・タスク管理機能も実装予定
- `.env` はGitHubに含めず、Koyeb Web UIで管理

---

## 📁 プロジェクト構成

```
discord-bot/
├── app/
│   ├── bot.py               # Discord Bot メインロジック
│   ├── cogs/                # 機能別Cogディレクトリ
│   │   ├── splatoon.py      # スプラトゥーン機能
│   │   ├── translate.py     # 翻訳機能
│   │   ├── qr.py            # QRコード機能
│   │   ├── reminder.py      # リマインダー機能
│   │   ├── calendar.py      # カレンダー機能（実装予定）
│   │   ├── tasks.py         # タスク管理機能（実装予定）
│   │   └── general.py       # 全般機能
│   └── services/            # サービス層
│       ├── translate_service.py # 翻訳サービス
│       ├── google_calendar.py   # Googleカレンダー連携
│       └── google_sheets.py     # Googleスプレッドシート連携

├── data/                    # データファイル保存用
│   ├── .gitkeep
│   ├── weapon_to_groups.json    # ブキデータ
│   ├── team_patterns.json       # 編成パターン
│   ├── reminders.json           # リマインダーデータ（自動生成）
│   ├── events.json              # カレンダー予定データ（自動生成）
│   └── tasks.json               # タスクデータ（自動生成）

├── docs/                    # ドキュメント
│   ├── SETUP.md
│   ├── FEATURES.md
│   ├── GOOGLE_CALENDAR_SETUP.md
│   ├── GOOGLE_SHEETS_SETUP.md

├── server.py                # FastAPI + Bot起動エントリーポイント
├── requirements.txt         # ライブラリ定義（翻訳機能含む）
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

### 🌐 翻訳機能
- `/translate <言語コード> <テキスト> [詳細表示]` - テキスト翻訳（ja, en, zh, fr, de, es対応）
- `/translate_help` - 翻訳機能のヘルプ
- 高精度翻訳（Google翻訳ベース）、シンプル表示・詳細表示選択、キャッシュ機能、レート制限付き

### 📱 QRコード機能
- `/qr_help` - QRコード機能のヘルプ
- `/qr <テキスト>` - QRコード生成（URL、テキストなど）

### ⏰ リマインダー機能
- `/remind_help` - リマインダー機能のヘルプ
- `/remind <時間> [メッセージ]` - 相対時間リマインダー（例: 5m, 1h, 2d）
- `/remind_at <日付> <時刻> [メッセージ]` - 絶対時間リマインダー（例: 明日 9:00）
- `/remind_list` - 設定中のリマインダー一覧表示
- `/remind_delete <ID>` - リマインダー削除
- `/remind_clear` - 全リマインダー削除（確認ダイアログ付き）
- Bot再起動後も継続される永続化対応
- スレッド内参加者への一括メンション機能（過去50件から取得）

### 🤖 全般機能
- `/help` - 全体のコマンド一覧
- `/ping` - Bot応答確認

## 🌐 翻訳機能の詳細

### 対応言語
| 言語コード | 言語名 | 国旗 |
|------------|--------|------|
| `ja` | 日本語 | 🇯🇵 |
| `en` | English | 🇺🇸 |
| `zh` | 中文 | 🇨🇳 |
| `fr` | Français | 🇫🇷 |
| `de` | Deutsch | 🇩🇪 |
| `es` | Español | 🇪🇸 |

### 使用制限
- **1分間**: 3回まで
- **1時間**: 20回まで
- **1日**: 50回まで
- **最大文字数**: 300文字

### 特徴
- **高精度翻訳**: Google翻訳ベースの高品質な翻訳
- **キャッシュ機能**: 同じテキストの翻訳は高速表示
- **自動言語検出**: 原文の言語を自動判定
- **使用統計表示**: 個人の使用状況を表示
- **レート制限**: サーバー負荷軽減のための制限機能

### 使用例
```
# シンプル表示（デフォルト）
/translate en 今日はいい天気ですね
→ It's nice weather today.

/translate ja How are you doing?
→ 調子はどう？

# 詳細表示（原文と言語情報も表示）
/translate en 今日はいい天気ですね show_details:True
→ 🇯🇵 → 🇺🇸
   原文: 今日はいい天気ですね
   翻訳: It's nice weather today.
```


---

## ✅ トラブルシュート

### 基本的な問題
| 症状 | 対策 |
|------|------|
| `KeyError: DISCORD_TOKEN` | Koyeb で環境変数が未設定 |
| Bot がスリープする | UptimeRobot で監視追加 |
| コマンドが補完されない | `/help` で確認、同期に時間がかかることも |

### 翻訳機能の問題
| 症状 | 対策 |
|------|------|
| 翻訳エラーが発生 | 一時的なAPI制限の可能性、時間をおいて再試行 |
| レート制限に達した | 使用制限を確認、時間経過後に再試行 |
| 翻訳結果が不正確 | テキストを短くする、句読点を調整 |
| タイムアウトエラー | テキストを短くして再試行 |

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
- [アーキテクチャ](docs/ARCHITECTURE.md) - システム構成とアーキテクチャ図
- [シーケンス図](docs/SEQUENCE_DIAGRAMS.md) - 機能別の処理フロー図

### 🛠️ 開発者向け
- [開発ガイド](docs/DEVELOPMENT_GUIDE.md) - 新機能追加時の完全チェックリスト

## 🧩 技術的特徴

### 🏗️ アーキテクチャ
- **FastAPI**: Web サーバーとして使用、将来的な API 拡張に対応
- **Cog ベース**: 機能別に分離された拡張可能な構成
- **サービス層**: 翻訳、Google 連携、ユーザー設定を独立したサービスとして管理
- **ハイブリッド データ管理**: ローカル JSON ファイルと Google サービスの自動切り替え
- **非同期処理**: 翻訳やAPI呼び出しの非同期実行でBot応答性を維持

### 🔄 データ管理
- **ローカル**: JSON ファイルでの軽量データ管理
- **Google 連携**: カレンダーとスプレッドシートでのクラウド同期
- **翻訳キャッシュ**: 翻訳結果のメモリキャッシュで高速化
- **使用統計**: ユーザー毎の翻訳使用量追跡とレート制限


## 🔧 新機能の追加方法

1. `app/cogs/` ディレクトリに新しいCogファイルを作成
2. `app/bot.py` の `setup_hook` メソッドで新しいCogを読み込み
3. 必要に応じて `requirements.txt` に依存関係を追加

## 📊 データファイルについて

### 自動生成されるファイル
- `data/reminders.json` - リマインダーデータ（永続化用）
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
    await self.load_extension("app.cogs.translate")
    await self.load_extension("app.cogs.qr")
    await self.load_extension("app.cogs.reminder")
    # await self.load_extension("app.cogs.calendar")  # 実装予定
    # await self.load_extension("app.cogs.tasks")     # 実装予定

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

### 🌐 翻訳機能の拡張
- **追加言語対応**: 韓国語、ロシア語、アラビア語など
- **翻訳履歴**: 過去の翻訳結果の保存・検索
- **一括翻訳**: 複数テキストの同時翻訳
- **音声翻訳**: 音声ファイルの翻訳対応

### 🌐 インターフェース
- **Web UI**: ブラウザからの管理画面
- **モバイル対応**: スマートフォン向け最適化
- **API 拡張**: REST API での外部連携

### 🌍 多言語・アクセシビリティ
- **Bot多言語対応**: Bot自体の英語やその他言語のサポート
- **タイムゾーン対応**: 地域別時刻表示
- **アクセシビリティ**: 視覚障害者向け対応
- **翻訳精度向上**: より高精度な翻訳エンジンの導入