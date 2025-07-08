# CFRP Monitor

複合材料（CFRP・GFRP・AFRP等）に関する最新情報を自動収集・分析するシステム

## 🔗 ダッシュボード

**<a href="https://mi2h1.github.io/cfrp-monitor/" target="_blank">📊 Live Dashboard</a>** - 収集データの可視化・分析

## 📋 システム概要

### 自動情報収集システム
- **10個の情報源**から毎日自動データ収集
- **学術論文** (arXiv、MDPI各誌) + **業界ニュース** (SAMPE、ACMA、AVK-TV等)
- **多言語対応** (英語・日本語・ドイツ語・中国語)
- **日本時間** でのタイムスタンプ管理

### データベース (Supabase)
- **itemsテーブル**: 収集された記事データ
- **sourcesテーブル**: 情報源管理
- **自動重複除去** & **本文スクレイピング**

### 自動化機能

#### 📅 日次実行 (GitHub Actions)
- 新着記事の自動収集
- 古いrawデータの自動削除 (30日経過後)

#### 🔍 週次実行 (毎日曜日)
- **新情報源の自動発見**
- 品質評価・自動承認
- Pull Request自動作成

## 🗂️ ファイル構成

```
cfrp-monitor/
├── README.md                    # このファイル
├── docs/                        # ダッシュボード
│   ├── index.html              # メインダッシュボード
│   └── config.js               # 設定ファイル
├── scripts/                     # Python スクリプト
│   ├── crawl.py                # 日次データ収集
│   ├── discover_*.py           # 情報源自動発見 (4ファイル)
│   ├── auto_approve_sources.py # 品質評価・自動承認
│   ├── rebuild_database.py     # データベース再構築
│   ├── cleanup_raw.py          # 古いデータ削除
│   └── fetcher.py              # データ取得ライブラリ
├── .github/workflows/           # GitHub Actions
│   ├── crawl.yml               # 日次クロール
│   └── discover_sources.yml    # 週次情報源発見
├── raw/                        # 生データ保管
│   └── YYYY-MM-DD/             # 日付別フォルダ
└── requirements.txt            # Python依存関係
```

## 🚀 情報源 (10個)

### 📰 業界ニュース (6個)
- **CompositesWorld** (US) - 複合材料業界最大手
- **SAMPE** (US) - 先進材料学会
- **ACMA** (US) - 米国複合材料製造業協会  
- **AVK-TV** (DE) - ドイツ複合材料協会
- **Manufacturing.net** (US) - 製造業情報
- **Chemical Processing** (US) - 化学工業情報

### 🔬 学術論文 (4個)
- **arXiv Enhanced** - 複合材料全般の学術論文
- **MDPI Composites Science** - 複合材料専門誌
- **MDPI Polymers** - ポリマー基複合材料
- **MDPI Materials** - 材料科学誌

## 🔧 技術スタック

- **Python 3** - データ収集・処理
- **Supabase** (PostgreSQL) - データベース
- **GitHub Actions** - 自動実行
- **HTML/JavaScript** - ダッシュボード
- **RSS/API** - データソース

## 📊 データフロー

```
情報源 (RSS/API) 
    ↓ 
日次クロール (crawl.py)
    ↓
データ処理 & 本文抽出
    ↓
Supabase データベース
    ↓
ダッシュボード表示
```

## ⚙️ 自動発見システム

### 🔍 発見手法
1. **Webスクレイピング** - 複合材料キーワード検索
2. **記事内リンク分析** - 既存記事からの参照先抽出
3. **多言語検索** - 中国語・ドイツ語・日本語対応
4. **学術データベース連携** - 人気著者・機関・学会の特定

### 📈 品質評価
- **関連度スコア** (70%重視)
- **ドメイン信頼性** (.edu, .org優遇)
- **更新頻度** & **言語多様性**
- **70点以上**: 自動承認
- **40-69点**: 手動レビュー

## 🕐 実行スケジュール

- **毎日 6:00 JST**: データ収集 + 古いrawデータ削除
- **毎週日曜**: 新情源発見 + 品質評価 + PR作成

---

**🤖 Powered by Claude Code - 自動化された複合材料情報モニタリングシステム**