-- sourcesテーブルに備考用のdescriptionカラムと更新日時カラムを追加

ALTER TABLE sources ADD COLUMN description TEXT;
ALTER TABLE sources ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- 既存データに現在時刻を設定
UPDATE sources SET updated_at = NOW() WHERE updated_at IS NULL;

-- 確認用: テーブル構造を表示
-- \d sources

-- 確認用: 既存データの確認
SELECT id, name, domain, description, updated_at 
FROM sources 
ORDER BY updated_at DESC
LIMIT 5;