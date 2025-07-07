# CFRP Monitor - sources テーブル移行ガイド

## 概要
seed_sources.yml から Supabase の sources テーブルベースの情報源管理に移行します。

## 移行手順

### 1. データベーススキーマ更新
```sql
-- Supabase SQLエディタで実行
\i migration/01_add_sources_columns.sql
```

### 2. 既存データの移行
```bash
# 環境変数設定
export SUPABASE_URL="your-supabase-url"
export SUPABASE_KEY="your-supabase-key"

# 移行スクリプト実行
python scripts/migrate_seed_sources.py
```

### 3. 新しいcrawl.pyのテスト
```bash
# テスト実行
python scripts/crawl.py
```

### 4. GitHub Actions更新
新しいcrawl.pyが正常動作することを確認後、GitHub Actionsで実行

## 変更点

### crawl.py
- **変更前**: `seed_sources.yml` から情報源を読み込み
- **変更後**: `sources` テーブルから `acquisition_mode='auto'` の情報源を取得

### データベース
- **追加カラム**: `name`, `urls`, `parser`, `ua`, `http_fallback`, `retry_count`, `backoff_factor`
- **外部キー**: `items.source_id` → `sources.id`

### 情報源管理
- **変更前**: YAMLファイルでの手動管理
- **変更後**: Supabaseテーブルでの管理（UI経由での更新可能）

## 利点

1. **動的管理**: 情報源の追加・削除・設定変更がコード変更不要
2. **UI管理**: Supabaseダッシュボードから情報源を管理可能
3. **関連性**: items と sources テーブルの正規化された関係
4. **監査証跡**: 情報源の変更履歴を追跡可能

## 注意点

- 移行後は `seed_sources.yml` は使用されなくなります
- 新しい情報源は直接 sources テーブルに追加してください
- `acquisition_mode='auto'` の情報源のみが自動収集されます