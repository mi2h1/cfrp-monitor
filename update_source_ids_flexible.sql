-- urlsが空のsourcesも考慮した柔軟なsource_id紐付けSQL

-- まず現在の状況を確認
SELECT 
  name,
  domain,
  urls,
  CASE 
    WHEN urls IS NULL OR array_length(urls, 1) IS NULL THEN 'URLs未設定'
    ELSE 'URLs設定済み'
  END as url_status
FROM sources
ORDER BY name;

-- 方法1: domainフィールドを使った紐付け（最も確実）
UPDATE items 
SET source_id = sources.id
FROM sources 
WHERE items.source_id IS NULL 
  AND sources.domain IS NOT NULL
  AND sources.domain = split_part(items.url, '/', 3);

-- 方法2: nameやcategoryから推測して手動マッピング
-- 例: CompositesWorldの場合
UPDATE items 
SET source_id = (SELECT id FROM sources WHERE name LIKE '%CompositesWorld%' LIMIT 1)
WHERE items.source_id IS NULL 
  AND items.url LIKE '%compositesworld%';

-- 例: arXivの場合  
UPDATE items 
SET source_id = (SELECT id FROM sources WHERE domain = 'arxiv.org' LIMIT 1)
WHERE items.source_id IS NULL 
  AND items.url LIKE '%arxiv.org%';

-- 方法3: src_typeとcategoryの照合
UPDATE items 
SET source_id = sources.id
FROM sources 
WHERE items.source_id IS NULL 
  AND items.src_type = sources.category
  AND sources.domain = split_part(items.url, '/', 3);

-- 方法4: 一般的なドメインパターンでの紐付け
UPDATE items 
SET source_id = sources.id
FROM sources 
WHERE items.source_id IS NULL 
  AND sources.domain IS NOT NULL
  AND items.url LIKE '%' || sources.domain || '%';

-- 確認用: 紐付けできなかったアイテムのドメイン一覧
SELECT 
  split_part(url, '/', 3) as domain,
  COUNT(*) as count,
  MIN(title) as sample_title
FROM items 
WHERE source_id IS NULL
GROUP BY split_part(url, '/', 3)
ORDER BY count DESC;

-- 確認用: sourcesテーブルの状況
SELECT 
  name,
  domain,
  category,
  CASE 
    WHEN urls IS NULL OR array_length(urls, 1) IS NULL THEN 'URLs未設定'
    ELSE array_length(urls, 1)::text || '個のURL'
  END as url_info
FROM sources
ORDER BY name;

-- 最終確認: 紐付け状況
SELECT 
  s.name as source_name,
  s.domain,
  COUNT(i.id) as item_count
FROM sources s
LEFT JOIN items i ON s.id = i.source_id
GROUP BY s.id, s.name, s.domain
ORDER BY item_count DESC;