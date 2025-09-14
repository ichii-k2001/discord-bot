# Googleカレンダー連携セットアップガイド

## 🎯 概要

Discord BotをGoogleカレンダーと連携させることで、以下の機能が利用できます：

- Discord上で追加した予定がGoogleカレンダーに自動同期
- Googleカレンダーの予定をDiscordで表示
- 双方向での予定管理

## 🔧 セットアップ手順

### 1. Google Cloud Console設定

#### 1.1 プロジェクト作成
1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 新しいプロジェクトを作成（または既存プロジェクトを選択）

#### 1.2 Calendar API有効化
1. 「APIとサービス」→「ライブラリ」に移動
2. "Google Calendar API" を検索
3. 「有効にする」をクリック

#### 1.3 認証情報作成
1. 「APIとサービス」→「認証情報」に移動
2. 「認証情報を作成」→「OAuth 2.0 クライアントID」を選択
3. アプリケーションの種類：「デスクトップアプリケーション」
4. 名前を入力（例：Discord Bot Calendar）
5. 「作成」をクリック
6. JSONファイルをダウンロード

### 2. プロジェクト設定

#### 2.1 認証情報ファイル配置
1. ダウンロードしたJSONファイルを `credentials.json` にリネーム
2. プロジェクトのルートディレクトリに配置

```
discord-bot/
├── credentials.json  ← ここに配置
├── app/
├── data/
└── ...
```

#### 2.2 環境変数設定
`.env` ファイルに以下を追加：

```env
# Google Calendar API連携
GOOGLE_CREDENTIALS_PATH=credentials.json
GOOGLE_CALENDAR_ID=primary
```

**カレンダーIDについて:**
- `primary`: メインカレンダー（デフォルト）
- 特定のカレンダーを使用する場合は、GoogleカレンダーでカレンダーIDを確認

### 3. 初回認証

#### 3.1 ローカル環境での認証
1. Botを起動
2. `/calendar_sync` コマンドを実行
3. 認証が必要な場合、コンソールにURLが表示される
4. ブラウザでURLにアクセスし、Googleアカウントで認証
5. 認証コードをコピーしてコンソールに入力

#### 3.2 本番環境での認証
本番環境（Koyeb等）では、事前にローカルで認証を完了し、生成された `data/token.json` をアップロードする必要があります。

## 🚀 使用方法

### 基本的な使い方

```bash
# 予定追加（Googleカレンダーに自動同期）
/calendar_add 会議 2025-01-15 14:30 プロジェクト進捗確認

# 予定一覧表示（Googleカレンダーから取得）
/calendar_list 7

# 同期状態確認
/calendar_sync
```

### 連携状態の確認

`/calendar_sync` コマンドで現在の連携状態を確認できます：

- ✅ **連携中**: Googleカレンダーと正常に連携
- ⚠️ **認証エラー**: 認証情報に問題あり
- 📋 **ローカルモード**: Googleカレンダー連携無効

## 🔒 セキュリティ

### 認証情報の管理

**重要**: 以下のファイルは機密情報を含むため、適切に管理してください：

- `credentials.json` - OAuth 2.0 クライアント情報
- `data/token.json` - アクセストークン（自動生成）

### .gitignore設定

```gitignore
# Google Calendar認証情報
credentials.json
data/token.json
```

## 🔧 トラブルシューティング

### よくある問題

**Q: 認証エラーが発生する**
A: 以下を確認してください：
- `credentials.json` が正しい場所に配置されているか
- Google Cloud ConsoleでCalendar APIが有効になっているか
- OAuth 2.0 クライアントIDが正しく設定されているか

**Q: 予定が同期されない**
A: 以下を確認してください：
- `/calendar_sync` で連携状態を確認
- カレンダーIDが正しく設定されているか
- 認証トークンが有効か（期限切れの場合は再認証）

**Q: 本番環境で認証できない**
A: 本番環境では対話的な認証ができないため、ローカルで認証を完了してから `data/token.json` をアップロードしてください。

### ログ確認

```bash
# デバッグモードでの実行
uvicorn server:app --host 0.0.0.0 --port 8080 --log-level debug
```

## 📊 機能制限

### 現在の制限事項

- 予定の編集機能は未実装
- 繰り返し予定の作成は未対応
- 複数カレンダーの同時管理は未対応

### 将来の拡張予定

- 予定編集機能
- 繰り返し予定対応
- 複数カレンダー管理
- 通知機能
- カレンダー共有機能

## 📞 サポート

問題が解決しない場合は、以下の情報と共にGitHubのIssuesで報告してください：

- エラーメッセージ
- 実行環境（ローカル/本番）
- 設定ファイルの内容（機密情報は除く）
- 実行したコマンド