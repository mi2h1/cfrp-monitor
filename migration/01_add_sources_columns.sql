-- sourcesテーブルにseed_sources.yml移行用のカラムを追加
-- 実行前に現在のスキーマをバックアップすることを推奨

-- 情報源名
ALTER TABLE public.sources ADD COLUMN IF NOT EXISTS
  name text;

-- RSS/API URL配列
ALTER TABLE public.sources ADD COLUMN IF NOT EXISTS
  urls text[];

-- パーサー設定（デフォルト: rss）
ALTER TABLE public.sources ADD COLUMN IF NOT EXISTS
  parser text DEFAULT 'rss';

-- User-Agent設定
ALTER TABLE public.sources ADD COLUMN IF NOT EXISTS
  ua text;

-- HTTPフォールバック設定
ALTER TABLE public.sources ADD COLUMN IF NOT EXISTS
  http_fallback boolean DEFAULT false;

-- リトライ回数設定
ALTER TABLE public.sources ADD COLUMN IF NOT EXISTS
  retry_count integer DEFAULT 3;

-- バックオフ係数設定
ALTER TABLE public.sources ADD COLUMN IF NOT EXISTS
  backoff_factor numeric DEFAULT 1.0;

-- インデックス追加（パフォーマンス向上）
CREATE INDEX IF NOT EXISTS idx_sources_acquisition_mode ON public.sources(acquisition_mode);
CREATE INDEX IF NOT EXISTS idx_sources_category ON public.sources(category);

-- 確認用クエリ
SELECT 
  column_name, 
  data_type, 
  is_nullable, 
  column_default
FROM information_schema.columns 
WHERE table_name = 'sources' 
  AND table_schema = 'public'
ORDER BY ordinal_position;