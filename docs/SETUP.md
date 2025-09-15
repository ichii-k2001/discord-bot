# セットアップガイド

## 🚀 クイックスタート

### 1. 環境準備

```bash
# リポジトリをクローン
git clone <your-repository-url>
cd discord-bot

# 仮想環境を作成・有効化
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# 依存関係をインストール
pip install -r requirements.txt
```

### 2. 環境変数設定

`.env.example` をコピーして `.env` を作成し、必要な環境変数を設定：

```bash
copy .env.example .env  # Windows
# cp .env.example .env  # macOS/Linux
```

`.env` ファイルを編集：
```env
DISCORD_TOKEN=your_actual_discord_token_here

# Google Calendar API連携（オプション）
GOOGLE_CREDENTIALS_PATH=credentials.json
GOOGLE_CALENDAR_ID=primary

# Google Sheets API連携（オプション）
GOOGLE_SPREADSHEET_ID=your_spreadsheet_id
GOOGLE_SHEET_NAME=Tasks
```

**必須設定:**
- `DISCORD_TOKEN`: Discord Bot のトークン

**オプション設定:**
- Google連携を使用しない場合は、Google関連の環境変数は設定不要
- ローカルJSONファイルでの動作が可能

### 3. ローカル実行

```bash
uvicorn server:app --host 0.0.0.0 --port 8080
```

ブラウザで http://localhost:8080 にアクセスして動作確認。

## 🔧 Discord Bot設定

### 1. Discord Developer Portal

1. https://discord.com/developers/applications にアクセス
2. 「New Application」をクリック
3. アプリケーション名を入力
4. 「Bot」タブに移動
5. 「Add Bot」をクリック
6. トークンをコピーして `.env` に設定

### 2. Bot権限設定

「OAuth2」→「URL Generator」で以下を選択：
- **Scopes**: `bot`, `applications.commands`
- **Bot Permissions**: 
  - Send Messages
  - Use Slash Commands
  - Read Message History
  - Embed Links

生成されたURLでBotをサーバーに招待。

## 📁 データファイル設定

### スプラトゥーン機能のカスタマイズ

`data/weapon_to_groups.json` と `data/team_patterns.json` を編集して、ブキデータや編成パターンをカスタマイズできます。

## 🌐 Koyebデプロイ

### 1. GitHub準備

```bash
git add .
git commit -m "Initial commit"
git push origin main
```

### 2. Koyeb設定

1. https://app.koyeb.com にアクセス
2. 「Create App」をクリック
3. GitHub連携を選択
4. リポジトリを選択
5. 環境変数 `DISCORD_TOKEN` を設定
6. デプロイ実行

### 3. 常時稼働設定

UptimeRobot等でKoyebのURLを定期監視設定。

## 🔍 トラブルシューティング

### よくある問題

**Q: コマンドが表示されない**
A: Discord側の同期に時間がかかる場合があります。最大1時間程度お待ちください。

**Q: データファイルが見つからない**
A: `data/` ディレクトリが存在することを確認してください。初回実行時に自動生成されます。

**Q: Google連携が動作しない**
A: 以下を確認してください：
- `credentials.json` が正しい場所に配置されているか
- 環境変数が正しく設定されているか
- `/calendar_sync` や `/task_sync` コマンドで状態を確認

**Q: プライバシー設定が反映されない**
A: `/privacy_status` で現在の設定を確認し、必要に応じて `/privacy_mode` で変更してください。

**Q: Botがオフラインになる**
A: UptimeRobotでの監視設定を確認してください。

### ログ確認

```bash
# ローカル実行時のログ確認
uvicorn server:app --host 0.0.0.0 --port 8080 --log-level debug
```

## 📞 サポート

問題が解決しない場合は、GitHubのIssuesで報告してください。