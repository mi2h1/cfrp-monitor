# CFRPモニター データベース構造

## 概要
このファイルは、CFRPモニターシステムのSupabaseデータベースの構造を記録しています。

## テーブル一覧

### 1. users テーブル
ユーザー情報を格納

### 2. sources テーブル
情報源（RSS、Webサイト等）を格納

### 3. task_logs テーブル
バッチ処理のログを格納

### 4. items テーブル
**記事データを格納するメインテーブル**

## 確認済みテーブル

### users テーブル
- `id` (UUID)
- `user_id` (string) - ユーザーID
- `display_name` (string) - 表示名
- `created_at` (timestamp)
- `last_login` (timestamp)
- `password_hash` (string)
- `password_salt` (string)
- `role` (string) - 権限 (admin/editor/viewer)

### sources テーブル
- `id` (UUID)
- `name` (string) - 情報源名
- `domain` (string)
- `category` (string)
- `country_code` (string)
- `relevance` (integer)
- `description` (string)
- `urls` (array)
- `policy_url` (string)
- `parser` (string)
- その他の設定フィールド

### task_logs テーブル
- `id` (UUID)
- `task_name` (string)
- `task_type` (string)
- `executed_at` (timestamp)
- `status` (string)
- `sources_processed` (integer)
- `articles_found` (integer)
- `articles_added` (integer)
- `errors_count` (integer)
- `details` (JSON)
- `duration_seconds` (integer)

### items テーブル
**記事データのメインテーブル**
- 構造詳細は追記予定

## 重要な注意事項
- 記事データは `articles` テーブルではなく `items` テーブルに格納されている
- APIの実装では `items` テーブルを使用する必要がある

## 更新履歴
- 2025-07-17: 初版作成、基本構造を記録
- 2025-07-17: itemsテーブルが記事データのメインテーブルであることを確認