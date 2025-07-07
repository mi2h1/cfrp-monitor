-- GitHub Pages（匿名アクセス）用のSupabase設定

-- 1. Row Level Security (RLS) を無効化（匿名アクセス許可）
ALTER TABLE public.items DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.sources DISABLE ROW LEVEL SECURITY;

-- 2. 匿名ユーザーに対する権限設定
-- anon ロールに SELECT, UPDATE 権限を付与
GRANT SELECT, UPDATE ON public.items TO anon;
GRANT SELECT ON public.sources TO anon;

-- 3. 必要に応じて INSERT, DELETE 権限も付与（管理者用）
-- GRANT INSERT, DELETE ON public.items TO anon;

-- 4. シーケンスへの権限付与（INSERT時に必要）
-- GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO anon;

-- 5. 確認用クエリ
SELECT 
  schemaname, 
  tablename, 
  rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
  AND tablename IN ('items', 'sources');

-- 現在の権限確認
SELECT 
  table_name,
  grantee,
  privilege_type
FROM information_schema.table_privileges 
WHERE table_schema = 'public' 
  AND table_name IN ('items', 'sources')
  AND grantee = 'anon';

-- 注意事項:
-- 本設定により、誰でもSupabase URLとキーがあればデータにアクセス可能になります
-- 本番環境では適切なセキュリティ設定を検討してください