# CFRP記事管理ダッシュボード セットアップガイド

## 概要
GitHub Pages + Supabase を使用した、複数人対応のログイン不要ダッシュボードです。

## セットアップ手順

### 1. データベーススキーマ更新
Supabase SQLエディタで以下を順番に実行：

```sql
-- items テーブルにフラグ管理用カラムを追加
\i migration/02_add_items_management_columns.sql

-- 匿名アクセスを有効化
\i migration/03_enable_anonymous_access.sql
```

### 2. Supabase設定の取得
1. Supabase プロジェクト → Settings → API
2. 以下の値をコピー：
   - Project URL
   - anon public key

### 3. HTMLファイルの設定
`docs/index.html` の以下の行を実際の値に置き換え：

```javascript
const SUPABASE_URL = 'YOUR_SUPABASE_URL';
const SUPABASE_ANON_KEY = 'YOUR_SUPABASE_ANON_KEY';
```

### 4. GitHub Pages の有効化
1. GitHub リポジトリ → Settings → Pages
2. Source: Deploy from a branch
3. Branch: main
4. Folder: /docs
5. Save

## 機能

### 記事管理
- **フィルタリング**: ステータス、重要フラグ、ソース別
- **ステータス管理**: 未読、確認済み、フラグ付き、アーカイブ
- **重要フラグ**: チェックボックスで設定
- **コメント**: 自由記述でメモ追加
- **リアルタイム保存**: 各記事個別に保存

### UI機能
- **レスポンシブデザイン**: モバイル対応
- **Bootstrap UI**: 使いやすいインターフェース
- **外部リンク**: 記事タイトルクリックで原文表示
- **自動更新**: 手動リフレッシュボタン

## 使用方法

### 基本操作
1. ダッシュボードにアクセス
2. フィルターで記事を絞り込み
3. 各記事のステータス・フラグ・コメントを設定
4. 「保存」ボタンで変更を保存

### フィルター
- **ステータス**: 未読/確認済み/フラグ付き/アーカイブ
- **重要**: 重要フラグの有無
- **ソース**: 情報源別

### ステータス管理
- **未読**: 新規記事（デフォルト）
- **確認済み**: 内容確認完了
- **フラグ付き**: 要注意・重要記事
- **アーカイブ**: 処理完了・非表示

## セキュリティ注意事項

- 匿名アクセスが有効なため、URLを知っていれば誰でもアクセス可能
- Supabase の anon key は公開されても安全ですが、適切な設定が重要
- 必要に応じてドメイン制限やIP制限を設定

## トラブルシューティング

### データが表示されない
1. Supabase URL/Key が正しく設定されているか確認
2. ブラウザの開発者ツールでエラーを確認
3. Supabaseの権限設定を確認

### 保存できない
1. 匿名アクセス設定が有効か確認
2. UPDATE権限が付与されているか確認

## アクセスURL
設定完了後、以下のURLでアクセス可能：
`https://USERNAME.github.io/cfrp-monitor/`