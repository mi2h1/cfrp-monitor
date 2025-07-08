-- acquisition_modeに'new'を追加

-- 既存の制約を削除
ALTER TABLE sources DROP CONSTRAINT IF EXISTS sources_acquisition_mode_check;

-- 新しい制約を追加（newを含める）
ALTER TABLE sources ADD CONSTRAINT sources_acquisition_mode_check 
    CHECK (acquisition_mode IN ('auto', 'manual', 'disabled', 'new'));

-- 確認用: 現在のacquisition_mode分布
SELECT acquisition_mode, COUNT(*) as count
FROM sources 
WHERE deleted = FALSE
GROUP BY acquisition_mode
ORDER BY acquisition_mode;

-- テスト用: newモードのサンプルデータ
-- UPDATE sources SET acquisition_mode = 'new' WHERE name = 'test source';

-- 確認用: acquisition_modeの制約確認
SELECT conname, pg_get_constraintdef(oid) as definition
FROM pg_constraint 
WHERE conrelid = 'sources'::regclass 
    AND conname LIKE '%acquisition_mode%';