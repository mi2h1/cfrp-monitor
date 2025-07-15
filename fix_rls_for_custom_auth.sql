-- Fix RLS for custom authentication system
-- Current system uses localStorage + custom users table, not Supabase Auth

-- Enable RLS on all tables first
ALTER TABLE public.items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.source_candidates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.task_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "authenticated_users_items" ON public.items;
DROP POLICY IF EXISTS "authenticated_users_sources" ON public.sources;
DROP POLICY IF EXISTS "authenticated_users_source_candidates" ON public.source_candidates;
DROP POLICY IF EXISTS "authenticated_users_task_logs" ON public.task_logs;
DROP POLICY IF EXISTS "users_own_data" ON public.users;
DROP POLICY IF EXISTS "service_role_access_items" ON public.items;
DROP POLICY IF EXISTS "service_role_access_sources" ON public.sources;
DROP POLICY IF EXISTS "service_role_access_source_candidates" ON public.source_candidates;
DROP POLICY IF EXISTS "service_role_access_task_logs" ON public.task_logs;
DROP POLICY IF EXISTS "service_role_access_users" ON public.users;

-- Create policies that allow access with service_role key
-- Since we're using anon key from frontend, we need to allow anon access
-- but in a real production environment, you'd want more restrictive policies

-- Allow anon access to items table (read/write)
CREATE POLICY "allow_anon_items" ON public.items
    FOR ALL USING (true);

-- Allow anon access to sources table (read/write)
CREATE POLICY "allow_anon_sources" ON public.sources
    FOR ALL USING (true);

-- Allow anon access to source_candidates table (read/write)
CREATE POLICY "allow_anon_source_candidates" ON public.source_candidates
    FOR ALL USING (true);

-- Allow anon access to task_logs table (read/write)
CREATE POLICY "allow_anon_task_logs" ON public.task_logs
    FOR ALL USING (true);

-- Allow anon access to users table (read/write)
CREATE POLICY "allow_anon_users" ON public.users
    FOR ALL USING (true);

-- Also allow service_role access for automated scripts
CREATE POLICY "service_role_items" ON public.items
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "service_role_sources" ON public.sources
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "service_role_source_candidates" ON public.source_candidates
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "service_role_task_logs" ON public.task_logs
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "service_role_users" ON public.users
    FOR ALL USING (auth.role() = 'service_role');