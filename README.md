# CFRP Monitor

CFRP（炭素繊維強化プラスチック）業界の最新情報を自動収集・管理するWebアプリケーション

**現在のバージョン**: v2025.01.08.12

## 🌐 システム概要

### 📰 記事管理ダッシュボード (`/articles`)
- 収集記事の閲覧・編集・管理（表形式リスト表示）
- ステータス管理（未読・確認済み・フラグ付き・アーカイブ）
- コメント・備考機能と重要度フラグ
- 高度なフィルタリング・ソート・ページネーション
- ロード中アニメーション付きスムーズなページ切り替え

### 📡 情報源管理ダッシュボード (`/sources`)
- 情報源リストと探索候補のタブ切り替え表示
- RSS URL編集・検証機能
- 取得モード制御（自動・手動・停止中・新規追加）
- 最終収集日時の監視・統計表示
- 新規候補の承認・却下・保留管理

### 👥 ユーザー管理ダッシュボード (`/users`)
- 管理者専用の新規ユーザー登録機能
- 役割ベース権限管理（admin/editor/viewer）
- ユーザー情報編集・削除機能
- ユーザー統計表示

## 🔐 認証・権限システム

### 認証方式
- **JWT認証**: セキュアなトークンベース認証
- **管理者制御登録**: 管理者による新規ユーザー作成
- **自動リダイレクト**: 未認証時は `/login` へ、認証済みは `/articles` へ
- **セッション管理**: 30分のタイムアウト機能

### 権限レベル
- **Admin**: 全機能アクセス（記事・情報源・ユーザー管理）
- **Editor**: 記事管理・情報源管理
- **Viewer**: 記事閲覧のみ

## 🚀 技術スタック

### フロントエンド
- **Vanilla JavaScript ES6+**: フレームワークレスSPA
- **Bootstrap 5.1.3**: レスポンシブUIフレームワーク
- **Font Awesome 6.5.1**: アイコンシステム
- **サイドバーナビゲーション**: ダークテーマ（#2c2c2c）
- **セキュリティ**: 本番環境での開発者ツール無効化

### バックエンド（Vercel Functions）
- **Python 3**: サーバーレス関数
- **Supabase PostgreSQL**: データベース
- **JWT認証**: トークンベースセキュリティ
- **RESTful API**: 標準的なHTTP APIエンドポイント

### 自動化システム（GitHub Actions）
- **日次クローリング**: 14:00 JST に自動実行
- **情報源発見**: 週次での新規ソース探索
- **候補管理**: 発見済み候補の自動処理

## 📊 データベーススキーマ

### メインテーブル
- **items**: 記事データ（タイトル・本文・URL・ステータス・コメント等）
- **sources**: 情報源管理（RSS URL・カテゴリ・取得モード・最終収集日時等）
- **users**: ユーザー認証（パスワードハッシュ・役割・表示名等）
- **source_candidates**: 探索候補管理（承認・却下・保留ステータス）
- **task_logs**: 自動実行ログ


## 🌍 情報源カバレッジ

### 📰 業界ニュース・協会
- 複合材料業界の最新ニュース・技術情報
- 学会・協会の発表・イベント情報
- メーカーのプレスリリース

### 🔬 学術論文・研究
- arXiv複合材料論文
- MDPI各誌（Composites Science、Polymers、Materials等）
- 大学・研究機関の発表

### 🏭 メーカー・企業情報
- 主要複合材料メーカーのニュース
- 新製品・技術発表
- 業界動向・市場情報

### 🌏 多言語・多地域対応
- **日本**: 東レ、帝人、日刊工業新聞等
- **アメリカ**: SAMPE、ACMA、CompositesWorld等
- **ヨーロッパ**: AVK-TV、Hexcel等
- **アジア**: 中国・韓国の複合材料情報

## 🗂️ ファイル構成

```
cfrp-monitor/
├── docs/                              # フロントエンド（Vercel Static）
│   ├── index.html                     # 認証状態ベースリダイレクト
│   ├── articles.html                  # 記事管理ダッシュボード
│   ├── sources.html                   # 情報源管理ダッシュボード
│   ├── users.html                     # ユーザー管理ダッシュボード
│   ├── login.html                     # ログインページ
│   └── assets/
│       ├── css/                       # モジュール化CSS
│       │   ├── common.css             # 共通スタイル
│       │   ├── sidebar.css            # サイドバーナビゲーション
│       │   ├── articles.css           # 記事管理画面
│       │   ├── sources.css            # 情報源管理画面
│       │   └── login.css              # ログイン画面
│       └── js/                        # モジュール化JavaScript
│           ├── common.js              # 共通機能（認証・ナビゲーション）
│           ├── page-init.js           # ページ初期化関数
│           ├── articles.js            # 記事管理機能
│           ├── sources.js             # 情報源管理機能
│           ├── users.js               # ユーザー管理機能
│           └── login.js               # ログイン機能
├── api/                               # バックエンドAPI（Vercel Functions）
│   ├── auth.py                        # JWT認証エンドポイント
│   ├── articles.py                    # 記事CRUD API
│   ├── sources.py                     # 情報源管理API
│   ├── users.py                       # ユーザー管理API
│   ├── source-candidates.py           # 候補管理API
│   └── layout.py                      # ナビゲーション・レイアウトAPI
├── scripts/                           # 自動化スクリプト
│   ├── crawl.py                       # メイン収集スクリプト
│   ├── discover_from_articles.py      # 記事からの情報源発見
│   ├── discover_multilingual_sources.py # 多言語情報源発見
│   ├── fetcher.py                     # RSS取得ライブラリ
│   ├── rss_validator.py              # RSS検証ツール
│   └── cleanup_raw.py                # 古いデータ削除
├── .github/workflows/                 # GitHub Actions
│   ├── crawl.yml                      # 日次クローリング
│   ├── discover_sources.yml           # 情報源発見
│   └── migrate_candidates.yml         # 候補移行
├── raw/                               # 日次収集データ保存
├── vercel.json                        # Vercelデプロイ設定
├── requirements.txt                   # Python依存関係
└── CLAUDE.md                          # 開発ガイドライン
```

## 📊 データフロー

```
RSS情報源（auto モード）
    ↓ GitHub Actions（日次14:00 JST）
Python収集スクリプト
    ↓ 重複除去・本文抽出
Supabase PostgreSQL
    ↓ Vercel Functions API
フロントエンドダッシュボード
    ↓ ユーザー編集（JWT認証）
データ更新・ステータス管理
```

## 🔧 運用・管理機能

### 情報源管理
- **自動RSS検証**: フィード形式・アクセス可能性チェック
- **新規候補発見**: 既存記事からの情報源自動発見
- **多言語探索**: 各言語での情報源自動発見
- **取得モード制御**: auto/manual/disabled/new での細かい制御
- **統計監視**: モード別カウント・最終収集日時表示

### セキュリティ
- **パスワードハッシュ化**: SHA-256 + ソルト
- **JWT認証**: セキュアなトークンベース認証
- **役割ベースアクセス制御**: 機能別権限管理
- **本番環境保護**: 開発者ツール無効化

### 監視・メンテナンス
- **収集ログ監視**: task_logs テーブルでの実行履歴
- **統計ダッシュボード**: 各種カウント表示
- **データ整合性**: 外部キー制約・バリデーション
- **自動バックアップ**: Supabase標準機能

## 🌐 デプロイ・アクセス

- **本番環境**: [https://cfrp-monitor.vercel.app/](https://cfrp-monitor.vercel.app/)
- **プラットフォーム**: Vercel + Supabase
- **自動デプロイ**: main ブランチプッシュ時
- **監視**: GitHub Actions ワークフロー状況

## 🔄 開発ワークフロー

1. **ローカル開発**: ブランチ作成・コード編集
2. **テスト**: API テストページでの動作確認
3. **コミット**: 標準的なコミットメッセージ
4. **デプロイ**: main ブランチマージで自動デプロイ
5. **監視**: 本番環境での動作確認

---

**🚀 Next Generation CFRP Information Monitoring System**  
**炭素繊維業界の情報収集を効率化する現代的なWebアプリケーション**