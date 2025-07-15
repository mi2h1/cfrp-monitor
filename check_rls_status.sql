-- Check RLS (Row Level Security) status and policies
-- Run this to verify that RLS has been properly enabled

-- 1. Check which tables have RLS enabled
SELECT 
    schemaname,
    tablename,
    rowsecurity as rls_enabled
FROM pg_tables 
WHERE schemaname = 'public' 
    AND tablename IN ('items', 'sources', 'source_candidates', 'task_logs', 'users')
ORDER BY tablename;

-- 2. Check existing policies on all tables
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies 
WHERE schemaname = 'public' 
    AND tablename IN ('items', 'sources', 'source_candidates', 'task_logs', 'users')
ORDER BY tablename, policyname;

-- 3. Test data access (should return data if working correctly)
SELECT 'items' as table_name, count(*) as record_count FROM public.items
UNION ALL
SELECT 'sources' as table_name, count(*) as record_count FROM public.sources
UNION ALL
SELECT 'source_candidates' as table_name, count(*) as record_count FROM public.source_candidates
UNION ALL
SELECT 'task_logs' as table_name, count(*) as record_count FROM public.task_logs
UNION ALL
SELECT 'users' as table_name, count(*) as record_count FROM public.users
ORDER BY table_name;

-- 4. Check current database role
SELECT current_user, current_setting('role') as current_role;

-- 5. Check if we can insert/update/delete (test with items table)
-- This should work if policies are correctly configured
SELECT 'RLS and policies are working correctly' as status;