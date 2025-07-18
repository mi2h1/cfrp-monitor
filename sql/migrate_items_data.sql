-- itemsテーブルからarticlesテーブルへのデータ移行SQL

-- 1. データ移行実行
INSERT INTO articles (
    id,
    source_id,
    title,
    url,
    body,
    published_at,
    src_type,
    status,
    flagged,
    comments,
    added_at,
    reviewed_at,
    last_edited_by,
    reviewer
)
SELECT 
    id,
    source_id,
    title,
    url,
    body,
    published_at,
    src_type,
    status,
    flagged,
    comments,
    added_at,
    reviewed_at,
    last_edited_by,
    reviewer
FROM items;

-- 2. 移行結果の確認
SELECT 
    'items' as table_name,
    COUNT(*) as record_count
FROM items
UNION ALL
SELECT 
    'articles' as table_name,
    COUNT(*) as record_count
FROM articles
ORDER BY table_name;

-- 3. 移行完了メッセージ
SELECT 
    CASE 
        WHEN (SELECT COUNT(*) FROM items) = (SELECT COUNT(*) FROM articles) 
        THEN '✅ データ移行が正常に完了しました！'
        ELSE '⚠️ 移行後の件数が一致しません。確認が必要です。'
    END as migration_status;