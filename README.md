# CFRP Monitor

複合材料（CFRP・GFRP・AFRP等）に関する最新情報を自動収集・管理するWebアプリケーション

## 🌐 Live Dashboard

### 📰 記事管理ダッシュボード
- 収集記事の閲覧・編集・管理
- ステータス管理（未読・確認済み・フラグ付き・アーカイブ）
- コメント機能・重要度フラグ
- 高度なフィルタリング・ソート機能

### 📡 情報源管理ダッシュボード  
- 情報源の監視・設定管理
- URL編集・RSS検証機能
- 取得モード制御（自動・手動・停止中・新規追加）
- 最終収集日時の表示

## 🔐 認証システム

- **ID認証**: シンプルなユーザーID方式
- **編集権限**: 認証ユーザーのみ記事・情報源の編集可能
- **セキュリティ**: Supabase RLS（Row Level Security）で保護

## 📊 システム概要

### 自動情報収集システム
- **複数の情報源**から定期的な自動データ収集
- **学術論文** + **業界ニュース** + **メーカー情報**
- **多言語対応** (英語・日本語・ドイツ語・中国語・韓国語)
- **日本時間（JST）** でのタイムスタンプ管理

### データベース (Supabase PostgreSQL)
- **itemsテーブル**: 収集記事データ（タイトル・本文・URL・ステータス等）
- **sourcesテーブル**: 情報源管理（URL・カテゴリ・取得モード・最終収集日時等）
- **usersテーブル**: ユーザー認証管理
- **自動重複除去** & **本文抽出**

### 取得モード
- **auto**: 自動収集対象（定時処理で記事を取得）
- **manual**: 手動確認のみ（自動収集しない）
- **disabled**: 停止中（一時的に無効化）
- **new**: 新規追加（RSS検証待ち）

## 🗂️ ファイル構成

```
cfrp-monitor/
├── README.md                          # このファイル
├── docs/                              # GitHub Pages ダッシュボード
│   ├── index.html                     # 記事管理（認証必須）
│   ├── sources.html                   # 情報源管理（認証必須）
│   ├── login.html                     # ログイン・新規登録
│   ├── common.css                     # 共通スタイル
│   ├── articles.css                   # 記事管理用スタイル
│   ├── sources.css                    # 情報源管理用スタイル
│   ├── common.js                      # 共通JavaScript（認証・Supabase）
│   ├── articles.js                    # 記事管理JavaScript
│   └── sources.js                     # 情報源管理JavaScript（開発中）
├── scripts/                           # Python自動化スクリプト
│   ├── add_*.py                       # 情報源追加スクリプト
│   ├── find_policy_urls*.py          # プライバシーポリシー自動検索
│   ├── verify_fix_urls.py            # URL検証・修正
│   ├── use_acquisition_mode_control.py # 取得モード制御
│   ├── add_html_scraping_support.py   # HTMLスクレイピング対応
│   └── update_collection_timestamp.py # 収集タイムスタンプ更新
├── *.sql                              # データベーススキーマ・設定ファイル
│   ├── setup_auth_*.sql              # 認証システム設定
│   ├── add_*.sql                     # カラム追加SQL
│   └── check_rls.sql                 # RLS権限確認
└── requirements.txt                   # Python依存関係
```

## 🌍 情報源カテゴリ

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

### 🌏 地域別
- **日本**: 東レ、帝人、三菱ケミカル等
- **アメリカ**: SAMPE、ACMA、CompositesWorld等
- **ヨーロッパ**: AVK-TV、Hexcel等
- **アジア**: 中国・韓国の複合材料情報

## 🔧 技術スタック

### フロントエンド
- **HTML5/CSS3/JavaScript ES6+**
- **Bootstrap 5** - UIフレームワーク
- **GitHub Pages** - 静的サイトホスティング

### バックエンド・データベース
- **Supabase** (PostgreSQL) - データベース・認証
- **Row Level Security (RLS)** - データアクセス制御
- **Real-time subscriptions** - リアルタイム更新

### 自動化・スクリプト
- **Python 3** - データ収集・処理
- **RSS/Atom フィード** - 記事取得
- **BeautifulSoup** - HTMLパース
- **Requests** - HTTP通信

## 📊 データフロー

```
情報源（RSS/HTML）
    ↓ Python スクリプト
データ収集・処理
    ↓ 重複除去・本文抽出
Supabase PostgreSQL
    ↓ Real-time API
ダッシュボード表示
    ↓ ユーザー編集
データ更新（JST）
```

## 🔍 情報源管理機能

### 自動検証
- **RSS検証**: フィード形式・アクセス可能性チェック
- **URL修正**: ドメイン・パス自動修正
- **プライバシーポリシー**: 自動検索・設定

### 手動管理
- **URL編集**: RSS URLの追加・編集・削除
- **取得モード変更**: auto/manual/disabled/new
- **備考・説明**: 情報源の詳細メモ
- **論理削除**: データ保持しつつ非表示化

### 統計・監視
- **収集統計**: モード別カウント表示
- **最終収集日時**: 自動収集の実行記録（新記事発見時のみ更新）
- **フィルタリング**: カテゴリ・国・モード・削除状態

## 🛡️ セキュリティ

### 認証・認可
- **ユーザー認証**: localStorage基盤の簡易認証
- **アクセス制御**: 未認証時は自動ログインページリダイレクト
- **データ保護**: Supabase RLS によるテーブルレベル保護

### データ管理
- **論理削除**: 物理削除せず削除フラグで管理
- **重複防止**: 情報源自動発見時の重複チェック
- **データ整合性**: 外部キー制約・バリデーション

## ⚙️ 運用・メンテナンス

### 定期メンテナンス
- 新情報源の追加・検証
- 無効URLの修正・削除
- 収集頻度の調整

### 監視項目
- 各情報源の収集成功率
- 新記事の取得状況
- システムエラー・例外

### バックアップ・復旧
- Supabaseの自動バックアップ
- 設定データのGit管理
- スクリプトによるデータ復旧

---

**🚀 Next Generation CFRP Information Monitoring System**  
**🤖 Powered by Claude Code - Intelligent Automation for Composite Materials Research**