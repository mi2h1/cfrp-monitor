# CFRP Monitor

CFRP（炭素繊維強化プラスチック）業界の最新情報を自動収集・管理するWebアプリケーション

**現在のバージョン**: v2025.01.08.13

## 🌟 主要機能

### 📰 記事管理システム
- **自動収集**: RSS/Webスクレイピングによる記事自動取得
- **AI要約**: Google Gemini APIによる記事内容の自動要約（300字）
- **ステータス管理**: 未読・確認済み・フラグ付き・アーカイブ
- **階層型コメント**: Reddit風のスレッド式コメント機能
- **高速ページネーション**: サーバーサイドページングとキャッシング

### 🤖 AI要約機能
- **構造化HTML解析**: 記事本文を正確に抽出
- **CFRP関連性チェック**: 無関連記事への自動警告
- **YAML構造化プロンプト**: 高品質な専門要約生成
- **データベース自動保存**: 要約結果の永続化

### 🎨 現代的なUI/UX
- **スケルトンローダー**: テーブル構造に対応した読み込み表示
- **レスポンシブデザイン**: モバイル・デスクトップ対応
- **記事詳細最適化**: AI要約に特化したレイアウト（左30%/右70%）

### 👥 ユーザー管理
- **役割ベース権限**: Admin/Editor/Viewer
- **JWT認証**: セキュアなトークンベース認証

## 🏗️ 技術スタック

### Frontend
- **Vanilla JavaScript**: フレームワークレスSPA
- **Bootstrap 5**: モダンなUIコンポーネント
- **Font Awesome**: 豊富なアイコンセット

### Backend
- **Vercel Functions**: Python製サーバーレス API
- **Supabase**: PostgreSQL データベース
- **Google Gemini API**: AI要約エンジン

### 自動化
- **GitHub Actions**: 日次クローリング（14:00 JST）
- **情報源発見**: 週次新規ソース探索

## 📊 データベース

### メインテーブル
- **articles**: 記事データ（ai_summaryカラム含む）
- **article_comments**: 階層型コメントシステム
- **sources**: 情報源管理
- **users**: ユーザー認証・権限

## 🌍 情報カバレッジ

### 📰 業界・技術情報
- 複合材料業界ニュース
- 学術論文・研究発表
- メーカープレスリリース

### 🌏 グローバル対応
- **日本**: 東レ、帝人、日刊工業新聞
- **アメリカ**: SAMPE、CompositesWorld
- **ヨーロッパ**: AVK-TV、Hexcel
- **アジア**: 中国・韓国複合材料情報

## 🚀 主要改善点（v2025.01.08.13）

### AI要約の大幅強化
- 構造化HTML解析による高精度コンテンツ抽出
- AI判定による最適記事内容選択
- CFRP関連性自動チェック機能

### UI/UX刷新
- 全スケルトンローダーの統一（スピナー廃止）
- 記事詳細レイアウトの AI要約特化設計
- ナビゲーション体験の改善

### コメント機能改善
- 最新返信による親コメント昇格ソート
- アクティブな議論の可視化

## 🔐 セキュリティ

- JWT認証によるトークンベースセキュリティ
- 役割ベースアクセス制御
- パスワードハッシュ化（SHA-256 + ソルト）

---

**🚀 Next Generation CFRP Information Monitoring System**  
**炭素繊維業界の情報収集を効率化する現代的なWebアプリケーション**