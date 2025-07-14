-- タスク実行ログを記録するテーブルを作成

-- 1. task_logsテーブルの作成
CREATE TABLE IF NOT EXISTS task_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    task_name TEXT NOT NULL,
    task_type TEXT DEFAULT 'daily_crawl',  -- daily_crawl, weekly_discover, manual など
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT DEFAULT 'success',  -- success, failed, partial
    
    -- 実行結果の詳細
    sources_processed INTEGER DEFAULT 0,
    articles_found INTEGER DEFAULT 0,
    articles_added INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0,
    
    -- その他の詳細情報（JSON形式）
    details JSONB,
    
    -- 実行時間
    duration_seconds INTEGER,
    
    -- インデックス
    CONSTRAINT task_logs_task_type_check CHECK (task_type IN ('daily_crawl', 'weekly_discover', 'manual', 'test'))
);

-- 2. インデックスを作成（検索高速化）
CREATE INDEX idx_task_logs_executed_at ON task_logs(executed_at DESC);
CREATE INDEX idx_task_logs_task_type ON task_logs(task_type);
CREATE INDEX idx_task_logs_status ON task_logs(status);

-- 3. RLSを有効化
ALTER TABLE task_logs ENABLE ROW LEVEL SECURITY;

-- 4. RLSポリシーを作成
-- 読み取りは全員可能
CREATE POLICY "task_logs_read_all" ON task_logs 
    FOR SELECT USING (true);

-- 挿入はanon権限でも可能（スクリプトから実行するため）
CREATE POLICY "task_logs_insert_anon" ON task_logs 
    FOR INSERT WITH CHECK (true);

-- 5. コメントを追加
COMMENT ON TABLE task_logs IS 'デイリータスクや定期実行の実行ログ';
COMMENT ON COLUMN task_logs.task_name IS 'タスク名（例: Daily Article Crawl）';
COMMENT ON COLUMN task_logs.task_type IS 'タスクの種類';
COMMENT ON COLUMN task_logs.executed_at IS '実行日時（JST）';
COMMENT ON COLUMN task_logs.sources_processed IS '処理した情報源の数';
COMMENT ON COLUMN task_logs.articles_found IS '発見した記事の総数';
COMMENT ON COLUMN task_logs.articles_added IS '新規追加した記事の数';
COMMENT ON COLUMN task_logs.details IS '詳細情報（エラー詳細、処理内容など）';

-- 6. テスト用のサンプルデータ挿入
INSERT INTO task_logs (
    task_name,
    task_type,
    status,
    sources_processed,
    articles_found,
    articles_added,
    details
) VALUES (
    'Daily Article Crawl - Test',
    'daily_crawl',
    'success',
    10,
    45,
    12,
    '{"sources": ["CompositesWorld", "arXiv"], "note": "テストデータ"}'::jsonb
);

-- 7. 確認
SELECT * FROM task_logs ORDER BY executed_at DESC;