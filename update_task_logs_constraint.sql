-- task_logsテーブルのtask_type制約を更新
-- 新しい週次発見タスクの種類を追加

-- 1. 既存の制約を削除
ALTER TABLE task_logs DROP CONSTRAINT task_logs_task_type_check;

-- 2. 新しい制約を追加（新しいタスクタイプを含む）
ALTER TABLE task_logs ADD CONSTRAINT task_logs_task_type_check 
CHECK (task_type IN (
    'daily_crawl',
    'weekly_discover',
    'weekly_source_discovery',
    'weekly_multilingual_discovery',
    'manual',
    'test'
));

-- 3. 更新されたスキーマを確認
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'task_logs'
ORDER BY ordinal_position;

-- 4. 制約の確認
SELECT conname, pg_get_constraintdef(oid) as constraint_definition
FROM pg_constraint 
WHERE conrelid = 'task_logs'::regclass 
AND contype = 'c';