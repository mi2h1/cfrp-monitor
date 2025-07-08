-- sourcesテーブルに論理削除用のdeletedフラグを追加

ALTER TABLE sources ADD COLUMN deleted BOOLEAN DEFAULT FALSE;

-- 既存データは全て削除されていない状態に設定
UPDATE sources SET deleted = FALSE WHERE deleted IS NULL;

-- 削除フラグでのフィルタリング用インデックス
CREATE INDEX idx_sources_deleted ON sources(deleted);

-- 確認用: 削除されていないソースの数を確認
SELECT 
    COUNT(*) FILTER (WHERE deleted = FALSE) as active_sources,
    COUNT(*) FILTER (WHERE deleted = TRUE) as deleted_sources,
    COUNT(*) as total_sources
FROM sources;