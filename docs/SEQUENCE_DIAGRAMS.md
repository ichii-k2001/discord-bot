# シーケンス図

## 🎯 概要

Discord Botの各機能における処理フローを詳細に示すシーケンス図集です。ユーザーの操作から最終的な応答まで、システム内部の動作を時系列で表現しています。

## 🚀 基本機能

### 1. Bot起動・初期化プロセス

```mermaid
sequenceDiagram
    participant K as Koyeb Platform
    participant F as FastAPI Server
    participant B as Discord Bot
    participant D as Discord API
    participant C as Cogs
    participant S as Services
    
    K->>F: アプリケーション起動
    F->>B: Bot インスタンス作成
    B->>B: 環境変数読み込み
    
    Note over B: setup_hook() 実行
    B->>C: Cog読み込み開始
    
    loop 各Cogの読み込み
        B->>C: load_extension()
        C->>S: サービス初期化
        S-->>C: 初期化完了
        C-->>B: Cog読み込み完了
    end
    
    B->>D: スラッシュコマンド同期
    D-->>B: 同期完了
    
    B->>D: Bot ログイン
    D-->>B: ログイン成功
    
    Note over B: on_ready イベント
    B->>B: 起動完了ログ出力
    
    F-->>K: ヘルスチェック応答開始
```

### 2. エラーハンドリング

```mermaid
sequenceDiagram
    participant U as User
    participant D as Discord
    participant B as Bot
    participant C as Cog
    participant S as Service
    participant L as Logger
    
    U->>D: コマンド実行
    D->>B: インタラクション受信
    B->>C: コマンド処理
    
    alt 正常処理
        C->>S: サービス呼び出し
        S-->>C: 処理結果
        C->>D: 成功応答
        D-->>U: 結果表示
    else サービスエラー
        C->>S: サービス呼び出し
        S-->>C: エラー発生
        C->>L: エラーログ記録
        C->>D: エラー応答（ephemeral）
        D-->>U: エラーメッセージ表示
    else 予期しないエラー
        C->>C: 例外発生
        C->>L: 例外ログ記録
        C->>D: 汎用エラー応答
        D-->>U: "予期しないエラーが発生しました"
    end
```

## 🌐 翻訳機能

### 3. 翻訳処理（成功パターン）

```mermaid
sequenceDiagram
    participant U as User
    participant D as Discord
    participant TC as TranslateCog
    participant TS as TranslateService
    participant C as Cache
    participant GT as Google Translate
    participant DB as Usage DB
    
    U->>D: /translate language:🇺🇸 English (en) text:こんにちは
    D->>TC: interaction受信
    TC->>D: defer()応答
    
    TC->>TS: translate_text(text, lang, user_id)
    
    Note over TS: 入力検証
    TS->>TS: 文字数チェック (≤300)
    TS->>TS: 言語コード検証
    
    Note over TS: レート制限チェック
    TS->>DB: ユーザー使用履歴取得
    TS->>TS: 制限内か判定
    
    Note over TS: キャッシュ確認
    TS->>C: キャッシュ検索
    
    alt キャッシュヒット
        C-->>TS: キャッシュ結果
        TS->>DB: 使用回数記録
        TS-->>TC: 翻訳結果（cached: true）
    else キャッシュミス
        TS->>GT: 翻訳API呼び出し
        GT-->>TS: 翻訳結果
        TS->>C: 結果をキャッシュ
        TS->>DB: 使用回数記録
        TS->>TS: 統計情報更新
        TS-->>TC: 翻訳結果（cached: false）
    end
    
    TC->>TC: Embed作成
    alt 詳細表示モード
        TC->>TC: 使用統計取得
        TC->>D: followup.send(embed)
        D-->>U: 詳細翻訳結果表示
    else シンプル表示モード（デフォルト）
        TC->>D: followup.send(text)
        D-->>U: 翻訳結果のみ表示
    end
```

### 4. 言語選択機能

```mermaid
sequenceDiagram
    participant U as User
    participant D as Discord
    participant TC as TranslateCog
    participant TS as TranslateService
    
    Note over U: /translate コマンド入力開始
    U->>D: /translate と入力
    D->>TC: コマンド補完要求
    
    TC->>TS: get_language_choices()
    TS->>TS: LANGUAGES辞書から選択肢生成
    
    loop 各言語
        TS->>TS: Choice(name="🇯🇵 日本語 (ja)", value="ja")
        TS->>TS: Choice(name="🇺🇸 English (en)", value="en")
        TS->>TS: Choice(name="🇨🇳 中文（简体） (zh-CN)", value="zh-CN")
        TS->>TS: Choice(name="🇹🇼 中文（繁體） (zh-TW)", value="zh-TW")
        TS->>TS: Choice(name="🇰🇷 한국어 (ko)", value="ko")
        Note over TS: その他の言語も同様
    end
    
    TS-->>TC: 選択肢リスト
    TC-->>D: 言語選択肢表示
    D-->>U: ドロップダウンメニュー表示
    
    U->>D: 言語選択（例：🇨🇳 中文（简体） (zh-CN)）
    D->>TC: 選択された値（zh-CN）
    
    Note over TC: 通常の翻訳処理へ続く
```

### 5. 翻訳エラー処理

```mermaid
sequenceDiagram
    participant U as User
    participant D as Discord
    participant TC as TranslateCog
    participant TS as TranslateService
    participant GT as Google Translate
    
    U->>D: /translate language:invalid text:長いテキスト...
    D->>TC: interaction受信
    TC->>D: defer()応答
    
    TC->>TS: translate_text()
    
    alt 文字数制限超過
        TS->>TS: len(text) > 300
        TS-->>TC: error: text_too_long
        TC->>D: エラーEmbed送信
        D-->>U: "テキストが長すぎます"
    else 無効な言語コード
        TS->>TS: 言語コード検証失敗
        TS-->>TC: error: invalid_language
        TC->>TC: 対応言語一覧作成
        TC->>D: エラーEmbed + 言語一覧
        D-->>U: "無効な言語コード + 対応言語"
    else レート制限
        TS->>TS: 使用制限チェック
        TS-->>TC: error: rate_limit
        TC->>D: エラーEmbed送信
        D-->>U: "使用制限に達しました"
    else API タイムアウト
        TS->>GT: 翻訳API呼び出し
        Note over GT: 8秒でタイムアウト
        GT-->>TS: TimeoutError
        TS-->>TC: error: timeout
        TC->>D: エラーEmbed送信
        D-->>U: "処理がタイムアウトしました"
    end
```

## 🎮 スプラトゥーン機能

### 5. チーム編成処理

```mermaid
sequenceDiagram
    participant U as User
    participant D as Discord
    participant SC as SplatoonCog
    participant WF as WeaponFormation
    participant JSON as JSON Files
    
    U->>D: /splatoon_team default
    D->>SC: interaction受信
    
    SC->>JSON: load_weapon_data()
    JSON-->>SC: ブキデータ
    SC->>JSON: load_team_patterns()
    JSON-->>SC: 編成パターン
    
    SC->>SC: パターン存在確認
    
    alt パターン存在
        SC->>SC: selected_structure取得
        
        Note over SC: アルファチーム編成
        loop 各ロールに対して
            SC->>SC: 候補ブキ抽出
            SC->>SC: ランダム選択
            SC->>SC: 使用済みセットに追加
        end
        
        Note over SC: ブラボチーム編成
        loop 各ロールに対して
            SC->>SC: 候補ブキ抽出（重複除外）
            SC->>SC: ランダム選択
            SC->>SC: 使用済みセットに追加
        end
        
        SC->>SC: 結果フォーマット
        SC->>D: 編成結果送信
        D-->>U: チーム編成表示
    else パターン不存在
        SC->>D: エラーメッセージ送信
        D-->>U: "パターンが存在しません"
    end
```

### 6. ブキ情報検索

```mermaid
sequenceDiagram
    participant U as User
    participant D as Discord
    participant WL as WeaponLookup
    participant JSON as JSON Files
    
    U->>D: /splatoon_weapon スプラシューター
    D->>WL: interaction受信
    
    WL->>JSON: weapon_data参照
    JSON-->>WL: ブキデータ
    
    WL->>WL: ブキ名で検索
    
    alt ブキ発見
        WL->>WL: ロール情報抽出
        WL->>WL: タイプ情報抽出
        WL->>WL: 応答フォーマット
        WL->>D: ブキ情報送信（ephemeral）
        D-->>U: ブキ詳細表示
    else ブキ未発見
        WL->>D: 未発見メッセージ送信
        D-->>U: "ブキが見つかりません"
    end
```

## 📱 QRコード機能

### 7. QRコード生成処理

```mermaid
sequenceDiagram
    participant U as User
    participant D as Discord
    participant QC as QRCog
    participant QR as QRCode Library
    participant IO as BytesIO
    
    U->>D: /qr https://example.com
    D->>QC: interaction受信
    
    QC->>QR: QRCode インスタンス作成
    QC->>QR: add_data(text)
    QC->>QR: make(fit=True)
    
    QC->>QR: make_image()
    QR-->>QC: PIL Image
    
    QC->>IO: BytesIO作成
    QC->>IO: image.save(buffer, 'PNG')
    QC->>IO: seek(0)
    
    QC->>QC: Discord File作成
    QC->>QC: Embed作成
    
    alt テキスト長い場合
        QC->>QC: テキスト省略（...）
    end
    
    QC->>QC: 生成者情報追加
    QC->>D: embed + file送信
    D-->>U: QRコード画像表示
```

## ⏰ リマインダー機能

### 8. リマインダー設定処理

```mermaid
sequenceDiagram
    participant U as User
    participant D as Discord
    participant RC as ReminderCog
    participant RM as ReminderManager
    participant JSON as JSON Files
    
    U->>D: /remind 30m 会議準備
    D->>RC: interaction受信
    
    RC->>RC: parse_time("30m")
    RC->>RC: 時間検証（≤30日）
    
    alt 有効な時間
        RC->>RC: target_time計算
        RC->>RC: スレッドユーザー取得（オプション）
        
        RC->>D: 設定完了メッセージ送信
        
        RC->>RM: add_reminder()
        RM->>JSON: リマインダー保存
        JSON-->>RM: 保存完了
        RM-->>RC: reminder_id
        
        RC->>D: メッセージ更新（ID追加）
        D-->>U: 設定完了 + ID表示
    else 無効な時間
        RC->>D: エラーメッセージ送信
        D-->>U: "時間形式が無効です"
    end
```

### 9. リマインダー実行（バックグラウンド）

```mermaid
sequenceDiagram
    participant BT as Background Task
    participant RM as ReminderManager
    participant JSON as JSON Files
    participant RC as ReminderCog
    participant D as Discord
    participant U as Users
    
    Note over BT: 1分間隔で実行
    BT->>RM: get_due_reminders()
    RM->>JSON: リマインダー読み込み
    JSON-->>RM: 全リマインダー
    RM->>RM: 期限チェック
    RM-->>BT: 期限到達リマインダー
    
    loop 各期限到達リマインダー
        BT->>RC: execute_reminder()
        RC->>D: get_channel()
        
        alt チャンネル存在
            RC->>RC: メンション文字列構築
            
            alt スレッドメンション有効
                RC->>RC: 他ユーザーメンション追加
            end
            
            RC->>D: リマインダーメッセージ送信
            D-->>U: ⏰ リマインダー通知
            
            BT->>RM: remove_reminder()
            RM->>JSON: リマインダー削除
        else チャンネル不存在
            Note over RC: ログ出力のみ
        end
    end
```

### 10. スレッドメンション処理

```mermaid
sequenceDiagram
    participant RC as ReminderCog
    participant D as Discord
    participant T as Thread Channel
    
    RC->>D: channel確認
    D-->>RC: Thread Channel
    
    RC->>T: history(limit=50)
    
    loop 過去50件のメッセージ
        T-->>RC: message
        RC->>RC: author.bot確認
        
        alt 人間のユーザー
            RC->>RC: user_id をセットに追加
        else Bot
            Note over RC: スキップ
        end
    end
    
    RC->>RC: 設定者を除外
    RC-->>RC: メンション対象ユーザーセット
```

## 📅 カレンダー機能

### 11. 予定追加（Google連携）

```mermaid
sequenceDiagram
    participant U as User
    participant D as Discord
    participant CC as CalendarCog
    participant GCS as GoogleCalendarService
    participant GCA as Google Calendar API
    participant JSON as JSON Files
    
    U->>D: /calendar_add 会議 2025-01-15 14:30
    D->>CC: interaction受信
    
    CC->>CC: 日付形式検証
    
    alt Google連携有効
        CC->>GCS: create_event()
        GCS->>GCA: イベント作成API
        GCA-->>GCS: Google Event
        GCS-->>CC: event_data + link
        
        CC->>JSON: ローカル保存
        JSON-->>CC: 保存完了
        
        CC->>CC: 応答作成（Google連携済み）
        CC->>D: 成功メッセージ + Googleリンク
        D-->>U: 予定追加完了 + リンク
    else Google連携無効
        CC->>JSON: ローカルのみ保存
        JSON-->>CC: 保存完了
        
        CC->>D: 成功メッセージ
        D-->>U: 予定追加完了
    end
```

### 12. 予定追加（ローカルのみ）

```mermaid
sequenceDiagram
    participant U as User
    participant D as Discord
    participant CC as CalendarCog
    participant JSON as JSON Files
    
    U->>D: /calendar_add 会議 2025-01-15
    D->>CC: interaction受信
    
    CC->>CC: 日付形式検証
    CC->>CC: イベントオブジェクト作成
    
    CC->>JSON: load_events()
    JSON-->>CC: 既存イベント
    
    CC->>CC: 新しいID生成
    CC->>CC: イベント追加
    
    CC->>JSON: save_events()
    JSON-->>CC: 保存完了
    
    CC->>CC: 応答フォーマット
    CC->>D: 成功メッセージ送信
    D-->>U: 予定追加完了
```

## 📋 タスク管理機能

### 13. タスク追加（Google連携）

```mermaid
sequenceDiagram
    participant U as User
    participant D as Discord
    participant TC as TaskCog
    participant GSS as GoogleSheetsService
    participant GSA as Google Sheets API
    participant JSON as JSON Files
    
    U->>D: /task_add レポート作成 2025-01-20 high
    D->>TC: interaction受信
    
    TC->>TC: 期限日付検証
    
    alt Google連携有効
        TC->>GSS: add_task()
        GSS->>GSA: スプレッドシート追加API
        GSA-->>GSS: 追加結果
        GSS-->>TC: task_id
        
        TC->>TC: 応答作成（Google連携済み）
        TC->>D: 成功メッセージ + シートリンク
        D-->>U: タスク追加完了 + リンク
    else Google連携無効
        TC->>JSON: ローカルのみ保存
        JSON-->>TC: 保存完了
        
        TC->>D: 成功メッセージ
        D-->>U: タスク追加完了
    end
```

### 14. タスク完了処理

```mermaid
sequenceDiagram
    participant U as User
    participant D as Discord
    participant TC as TaskCog
    participant GSS as GoogleSheetsService
    participant GSA as Google Sheets API
    participant JSON as JSON Files
    
    U->>D: /task_complete 123
    D->>TC: interaction受信
    
    alt Google連携有効
        TC->>GSS: get_tasks()
        GSS->>GSA: スプレッドシート取得API
        GSA-->>GSS: タスクリスト
        GSS-->>TC: タスクデータ
        
        TC->>TC: task_id検索
        
        alt タスク存在
            alt 未完了タスク
                TC->>GSS: update_task_status(id, "completed")
                GSS->>GSA: ステータス更新API
                GSA-->>GSS: 更新結果
                GSS-->>TC: 成功
                
                TC->>D: 完了メッセージ送信
                D-->>U: "タスクを完了しました"
            else 既に完了済み
                TC->>D: 警告メッセージ送信
                D-->>U: "既に完了済みです"
            end
        else タスク不存在
            TC->>D: エラーメッセージ送信
            D-->>U: "タスクが見つかりません"
        end
    else ローカルのみ
        TC->>JSON: タスク検索・更新
        JSON-->>TC: 更新結果
        TC->>D: 結果メッセージ送信
        D-->>U: 処理結果
    end
```

## 🔄 共通処理

### 15. Google API認証

```mermaid
sequenceDiagram
    participant S as Service
    participant F as File System
    participant G as Google API
    participant T as Token Storage
    
    S->>S: authenticate()呼び出し
    S->>F: credentials.json確認
    
    alt 認証情報存在
        F-->>S: credentials.json
        S->>T: 既存トークン確認
        
        alt 有効なトークン存在
            T-->>S: access_token
            S->>G: API呼び出しテスト
            G-->>S: 成功応答
            S-->>S: 認証成功
        else トークン期限切れ
            S->>G: トークンリフレッシュ
            G-->>S: 新しいトークン
            S->>T: トークン保存
            S-->>S: 認証成功
        else トークン不存在
            S->>G: 初回認証フロー
            G-->>S: 認証URL
            Note over S: ユーザー認証必要
            G-->>S: 認証コード
            S->>G: トークン取得
            G-->>S: access_token
            S->>T: トークン保存
            S-->>S: 認証成功
        end
    else 認証情報不存在
        S-->>S: 認証失敗
    end
```

### 16. データ同期処理

```mermaid
sequenceDiagram
    participant L as Local Storage
    participant S as Service
    participant G as Google API
    participant C as Cache
    
    Note over S: データ取得要求
    S->>S: Google連携確認
    
    alt Google連携有効
        S->>G: データ取得API
        
        alt API成功
            G-->>S: Googleデータ
            S->>C: キャッシュ更新
            S->>L: ローカル同期（オプション）
            S-->>S: Googleデータ返却
        else API失敗
            S->>L: ローカルデータ取得
            L-->>S: ローカルデータ
            S-->>S: ローカルデータ返却
        end
    else Google連携無効
        S->>L: ローカルデータ取得
        L-->>S: ローカルデータ
        S-->>S: ローカルデータ返却
    end
    
    Note over S: データ保存要求
    S->>S: Google連携確認
    
    alt Google連携有効
        S->>G: データ保存API
        S->>L: ローカル保存（バックアップ）
        
        alt API成功
            G-->>S: 保存成功
            S->>C: キャッシュ更新
            S-->>S: 保存完了
        else API失敗
            Note over S: ローカルのみ保存継続
            S-->>S: ローカル保存完了
        end
    else Google連携無効
        S->>L: ローカル保存
        L-->>S: 保存完了
        S-->>S: 保存完了
    end
```

## 📊 パフォーマンス考慮事項

### 応答時間の最適化
- **キャッシュ活用**: 翻訳結果の再利用
- **非同期処理**: API呼び出しの並列実行
- **defer応答**: 長時間処理の応答性確保

### エラー回復
- **フォールバック**: Google API失敗時のローカル処理
- **リトライ**: 一時的な障害への対応
- **タイムアウト**: 無限待機の防止

### リソース管理
- **メモリ制限**: キャッシュサイズの制御
- **ファイルI/O**: JSON読み書きの最適化
- **API制限**: レート制限の遵守