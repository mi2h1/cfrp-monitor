# Claude開発ガイドライン

このファイルは、CFRP Monitorプロジェクトの開発作業における重要な決まり事とベストプラクティスをまとめたものです。毎回の作業開始前に確認してください。

## 🎯 基本方針

### 作業開始前の必須確認事項
- **CLAUDE.mdを読む** - このファイルで決まり事を確認
- **database-schema-complete.mdを読む** - DBスキーマを理解してから作業開始
- **SYSTEM_TECHNICAL_SPECIFICATION.mdを読む** - システム全体の技術構成を理解してから作業開始
- **現在の作業内容を把握** - 前回の作業内容と今回の目標を明確にする
- **会話は日本語で行う** - ユーザーとの会話は必ず日本語を使用する

### 作業フロー
- **作業完了後は必ずプッシュする** - 開発環境がないため、作業完了後は毎回必ずgit pushを実行
- **TodoWriteツールを積極的に使用** - 複数ステップの作業は必ずtodoで管理し、進捗を可視化
- **簡潔な回答を心がける** - ユーザーの質問には4行以内で回答（コード生成は除く）

### 作業終了時の必須作業
- **ドキュメント更新の実施** - 作業完了後は必ず以下のドキュメントを最新の実装に合わせて更新する
  - `database-schema-complete.md` - データベーススキーマの変更があった場合
  - `SYSTEM_TECHNICAL_SPECIFICATION.md` - 機能追加・変更・技術構成の変更があった場合
- **実装項目の正確な反映** - デタラメな記載は厳禁。実際のコードを確認して正確に記載する
- **変更履歴の記録** - 各ドキュメントの更新履歴セクションに変更内容と日付を記録する

### UI/UX設計
- **Font Awesomeアイコンを使用** - 絵文字は使わず、必ずFont Awesome（`<i class="fas fa-xxx"></i>`）を使用
- **Bootstrap 5を活用** - 既存のBootstrap 5クラスを最大限活用
- **レスポンシブデザイン** - モバイル対応を常に考慮
- **一貫性の保持** - 既存のデザインパターンに合わせる

## 📝 コーディング規約

### CSS/スタイル
- **text-truncateのoverflow** - `overflow: clip`を使用（パフォーマンス向上）
- **アイコンの間隔** - アイコンとテキストの間は`me-2`クラスで統一
- **垂直位置調整** - `vertical-align: middle`でアイコンとテキストを揃える

### JavaScript
- **セキュリティ** - HTMLエスケープ処理を必ず実施
- **エラーハンドリング** - try-catch文を適切に使用
- **API通信** - 認証トークンを適切に管理
- **空値処理** - 空文字列の場合は`null`として送信
- **日時処理** - 必ず`timezone-utils.js`の関数を使用（JST統一）
  - 表示: `formatJSTDisplay()`, `formatJSTDate()`, `formatJSTRelative()`
  - 現在時刻: `nowJST()`, `nowJSTISO()`, `todayJST()`

### バックエンド（Python）
- **空値の更新** - `'field' in data`で空文字列も更新対象に含める
- **認証チェック** - 全APIで適切な認証処理を実装
- **エラーレスポンス** - 適切なHTTPステータスコードとエラーメッセージを返す
- **日時処理** - 必ず`utils/timezone_utils.py`の関数を使用（JST統一）
  - DB書き込み: `now_jst_naive_iso()`, `today_jst_iso()`
  - 表示変換: `format_jst_display()`, `parse_to_jst()`

## 🚀 アーキテクチャ

### 技術スタック
- **フロントエンド**: HTML5, CSS3, JavaScript (ES6+), Bootstrap 5, Font Awesome
- **バックエンド**: Python (Vercel Functions), Supabase
- **認証**: JWT
- **デプロイ**: Vercel

### ディレクトリ構造
```
docs/                  # 静的ファイル
├── assets/
│   ├── css/          # スタイルシート
│   └── js/           # JavaScript
├── *.html            # HTMLページ
api/                  # Vercel Functions
├── *.py              # Python API
vercel.json          # Vercel設定
```

### 権限管理
- **admin**: 全機能アクセス可能
- **editor**: 記事・情報源管理可能
- **viewer**: 記事閲覧のみ

## 🗃️ データベース構造（重要）

### メインテーブル
- **articles**: 記事データ（旧itemsテーブル）（id, source_id, title, url, body, published_at, status, flagged, comments, added_at, reviewed_at, last_edited_by, reviewer）
- **sources**: 情報源（id, name, domain, category, country_code, relevance, urls, acquisition_mode, deleted, etc.）
- **users**: ユーザー（user_id, display_name, role, password_hash, created_at, etc.）
- **source_candidates**: 探索候補（id, name, domain, urls, relevance_score, status, discovery_method, etc.）

### 重要な関係性
- articles.source_id → sources.id（外部キー）
- articles.status: 'unread', 'reviewed', 'flagged', 'archived'
- sources.acquisition_mode: 'auto', 'manual', 'disabled'
- users.role: 'admin', 'editor', 'viewer'

**詳細は必ずdatabase-schema-complete.mdを確認すること！**

## 🔧 開発時の注意点

### Git管理
- **コミットメッセージ**: 英語で簡潔に、日本語でも詳細を記載
- **ブランチ戦略**: mainブランチで直接開発
- **プッシュタイミング**: 作業完了後は必ずプッシュ

### セキュリティ
- **認証トークン**: localStorageで管理、適切な検証を実装
- **XSS対策**: HTMLエスケープ処理を徹底
- **API保護**: 全エンドポイントで認証チェック

### パフォーマンス
- **画像最適化**: 適切なサイズと形式を使用
- **CSS最適化**: 不要なスタイルは削除
- **JavaScript最適化**: 重複コードを避ける

## 📋 よくある作業パターン

### 新機能追加
1. TodoWriteで作業を分解
2. HTMLで画面を作成
3. JavaScriptで機能を実装
4. APIを作成・更新
5. テスト実行
6. コミット＆プッシュ

### バグ修正
1. 問題の特定と原因調査
2. 修正方針の決定
3. 実装
4. テスト
5. コミット＆プッシュ

### UI改善
1. Font Awesomeアイコンの活用
2. Bootstrap 5クラスの活用
3. レスポンシブ対応の確認
4. 一貫性の保持

## 🎨 デザイン方針

### カラーパレット
- **プライマリ**: Bootstrap 5のblue系
- **サイドバー**: #2c2c2c（ダークグレー）
- **成功**: green系
- **警告**: yellow系
- **エラー**: red系

### レイアウト
- **サイドバー**: 固定幅250px、左側配置
- **メインコンテンツ**: サイドバー分の左マージン
- **カード**: 統一されたスタイル

## 📅 重要な変更履歴
- **2025-07-17**: 完全なデータベース構造を記録
- **2025-07-18**: Font Awesomeアイコン統一とUI改善決定
- **2025-07-18**: itemsテーブルをarticlesテーブルに名前変更
- **2025-07-18**: JST日時処理統一（timezone_utils導入）

---

**最終更新**: 2025年7月18日
**プロジェクト**: CFRP Monitor v2025.01.08.12