-- itemsテーブルにフラグ管理・コメント機能用のカラムを追加

-- ステータス管理（未読、確認済み、アーカイブ等）
ALTER TABLE public.items ADD COLUMN IF NOT EXISTS
  status text DEFAULT 'unread';

-- コメント
ALTER TABLE public.items ADD COLUMN IF NOT EXISTS
  comments text;

-- 重要フラグ
ALTER TABLE public.items ADD COLUMN IF NOT EXISTS
  flagged boolean DEFAULT false;

-- レビュー日時
ALTER TABLE public.items ADD COLUMN IF NOT EXISTS
  reviewed_at timestamp with time zone;

-- レビュアー名
ALTER TABLE public.items ADD COLUMN IF NOT EXISTS
  reviewer text;

-- インデックス追加（パフォーマンス向上）
CREATE INDEX IF NOT EXISTS idx_items_status ON public.items(status);
CREATE INDEX IF NOT EXISTS idx_items_flagged ON public.items(flagged);
CREATE INDEX IF NOT EXISTS idx_items_reviewed_at ON public.items(reviewed_at);

-- ステータス用の制約追加（オプション）
ALTER TABLE public.items ADD CONSTRAINT check_status 
CHECK (status IN ('unread', 'reviewed', 'flagged', 'archived'));

-- 確認用クエリ
SELECT 
  column_name, 
  data_type, 
  is_nullable, 
  column_default
FROM information_schema.columns 
WHERE table_name = 'items' 
  AND table_schema = 'public'
  AND column_name IN ('status', 'comments', 'flagged', 'reviewed_at', 'reviewer')
ORDER BY ordinal_position;