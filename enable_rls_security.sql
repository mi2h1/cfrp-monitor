-- Enable Row Level Security (RLS) for all tables
-- This is required for security when using Supabase's PostgREST API

-- Enable RLS on items table
ALTER TABLE public.items ENABLE ROW LEVEL SECURITY;

-- Enable RLS on sources table
ALTER TABLE public.sources ENABLE ROW LEVEL SECURITY;

-- Enable RLS on source_candidates table
ALTER TABLE public.source_candidates ENABLE ROW LEVEL SECURITY;

-- Enable RLS on task_logs table
ALTER TABLE public.task_logs ENABLE ROW LEVEL SECURITY;

-- Enable RLS on users table (already enabled but ensure it's there)
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Create policies for authenticated users
-- Policy for items table - authenticated users can read and write
CREATE POLICY "authenticated_users_items" ON public.items
    FOR ALL USING (auth.role() = 'authenticated');

-- Policy for sources table - authenticated users can read and write
CREATE POLICY "authenticated_users_sources" ON public.sources
    FOR ALL USING (auth.role() = 'authenticated');

-- Policy for source_candidates table - authenticated users can read and write
CREATE POLICY "authenticated_users_source_candidates" ON public.source_candidates
    FOR ALL USING (auth.role() = 'authenticated');

-- Policy for task_logs table - authenticated users can read and write
CREATE POLICY "authenticated_users_task_logs" ON public.task_logs
    FOR ALL USING (auth.role() = 'authenticated');

-- Policy for users table - users can only access their own data
CREATE POLICY "users_own_data" ON public.users
    FOR ALL USING (auth.role() = 'authenticated');

-- Alternative: If using service role for automated scripts
-- You might want to allow service role access as well
CREATE POLICY "service_role_access_items" ON public.items
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "service_role_access_sources" ON public.sources
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "service_role_access_source_candidates" ON public.source_candidates
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "service_role_access_task_logs" ON public.task_logs
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "service_role_access_users" ON public.users
    FOR ALL USING (auth.role() = 'service_role');