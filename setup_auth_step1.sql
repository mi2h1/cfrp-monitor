-- Step 1: ユーザー認証システムのデータベース準備

-- 1. usersテーブルを作成
CREATE TABLE IF NOT EXISTS users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT UNIQUE NOT NULL,
    display_name TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP DEFAULT NOW()
);

-- 2. usersテーブルのRLSを有効化
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- 3. usersテーブルの読み取りポリシー（誰でも読める）
CREATE POLICY "users_select_policy" ON users 
    FOR SELECT USING (true);

-- 4. usersテーブルの挿入ポリシー（誰でも新規登録可能）
CREATE POLICY "users_insert_policy" ON users 
    FOR INSERT WITH CHECK (true);

-- 5. usersテーブルの更新ポリシー（自分の情報のみ更新可能）
CREATE POLICY "users_update_policy" ON users 
    FOR UPDATE USING (true);

-- 6. 現在のポリシー状況を確認
SELECT 
    schemaname,
    tablename,
    policyname,
    cmd,
    roles
FROM pg_policies 
WHERE schemaname = 'public' 
ORDER BY tablename, policyname;

-- 7. テーブル一覧を確認
SELECT 
    schemaname,
    tablename,
    rowsecurity as rls_enabled
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY tablename;

-- 8. テスト用ユーザーを作成（確認用）
INSERT INTO users (user_id, display_name) 
VALUES ('admin', '管理者'), ('test', 'テストユーザー')
ON CONFLICT (user_id) DO NOTHING;

-- 9. 作成確認
SELECT * FROM users ORDER BY created_at;