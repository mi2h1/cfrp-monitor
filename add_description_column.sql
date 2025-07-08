-- sourcesテーブルに備考用のdescriptionカラムを追加

ALTER TABLE sources ADD COLUMN description TEXT;

-- 確認用: テーブル構造を表示
-- \d sources

-- 確認用: 既存データの確認
SELECT id, name, domain, description 
FROM sources 
LIMIT 5;