-- 編集者記録機能を追加

-- 1. itemsテーブルにlast_edited_byカラムを追加
ALTER TABLE items 
ADD COLUMN last_edited_by TEXT;

-- 2. sourcesテーブルにlast_edited_byカラムを追加
ALTER TABLE sources 
ADD COLUMN last_edited_by TEXT;

-- 3. usersテーブルとの関連を設定（外部キー制約は設定しない - 簡易認証のため）
COMMENT ON COLUMN items.last_edited_by IS '最終編集者のユーザーID';
COMMENT ON COLUMN sources.last_edited_by IS '最終編集者のユーザーID';

-- 4. 確認
SELECT 
    table_name,
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns 
WHERE table_name IN ('items', 'sources') 
    AND column_name = 'last_edited_by'
ORDER BY table_name;

-- 5. テスト用のサンプル更新
-- UPDATE items 
-- SET last_edited_by = 'test_user', reviewed_at = NOW() 
-- WHERE id = 'item_id_here';

-- UPDATE sources 
-- SET last_edited_by = 'test_user', updated_at = NOW() 
-- WHERE id = 'source_id_here';