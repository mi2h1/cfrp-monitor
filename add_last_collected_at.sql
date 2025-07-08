-- 自動収集の最終実行日時を記録するカラムを追加

-- 1. last_collected_atカラムを追加
ALTER TABLE sources 
ADD COLUMN last_collected_at TIMESTAMP WITH TIME ZONE;

-- 2. カラムにコメントを追加
COMMENT ON COLUMN sources.last_collected_at IS '最終自動収集実行日時（新しい記事が見つかった場合のみ更新）';

-- 3. 確認
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'sources' 
    AND column_name = 'last_collected_at';

-- 4. テスト用のサンプル更新（実際の定時処理で使用する形式）
-- UPDATE sources 
-- SET last_collected_at = NOW() 
-- WHERE id = 'source_id_here' AND acquisition_mode = 'auto';