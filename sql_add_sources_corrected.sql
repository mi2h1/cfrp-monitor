-- 正しいテーブル構造に合わせた新規情報源追加SQL
-- 実際のsourcesテーブル構造に完全対応

-- 1. arXiv 中国関連複合材料検索（最優先）
INSERT INTO sources (name, urls, parser, acquisition_mode, category, domain, country_code)
VALUES (
    'arXiv - China Composites Research',
    ARRAY['https://export.arxiv.org/api/query?search_query=all:"composite materials"+AND+all:china&max_results=20&sortBy=submittedDate&sortOrder=descending'],
    'rss',
    'auto',
    'paper',
    'arxiv.org',
    'US'
);

-- 2. arXiv 拡張複合材料検索（GFRP, AFRP含む）
INSERT INTO sources (name, urls, parser, acquisition_mode, category, domain, country_code)
VALUES (
    'arXiv - Enhanced Composites Search',
    ARRAY['https://export.arxiv.org/api/query?search_query=all:"composite materials"+OR+all:GFRP+OR+all:AFRP+OR+all:"fiber reinforced"+OR+all:"metal matrix"&max_results=50&sortBy=submittedDate&sortOrder=descending'],
    'rss',
    'auto',
    'paper',
    'arxiv.org',
    'US'
);

-- 3. ドイツ複合材料協会 AVK-TV（ヨーロッパ情報）
INSERT INTO sources (name, urls, parser, acquisition_mode, category, domain, country_code, relevance)
VALUES (
    'AVK-TV (German Composites Association)',
    ARRAY['https://avk-tv.de/feed'],
    'rss',
    'auto',
    'news',
    'avk-tv.de',
    'DE',
    9
);

-- 4. SAMPE 先進材料学会
INSERT INTO sources (name, urls, parser, acquisition_mode, category, domain, country_code, relevance)
VALUES (
    'SAMPE - Advanced Materials Society',
    ARRAY['https://sampe.org/feed'],
    'rss',
    'auto',
    'news',
    'sampe.org',
    'US',
    10
);

-- 5. ACMA - 米国複合材料製造業協会
INSERT INTO sources (name, urls, parser, acquisition_mode, category, domain, country_code, relevance)
VALUES (
    'ACMA - American Composites Manufacturers',
    ARRAY['https://acmanet.org/feed'],
    'rss',
    'auto',
    'news',
    'acmanet.org',
    'US',
    9
);

-- 6. MDPI Journal of Composites Science（複合材料専門誌）
INSERT INTO sources (name, urls, parser, acquisition_mode, category, domain, country_code, relevance)
VALUES (
    'MDPI Journal of Composites Science',
    ARRAY['https://www.mdpi.com/rss/journal/jcs'],
    'rss',
    'auto',
    'paper',
    'mdpi.com',
    'CH',
    9
);

-- 7. MDPI Polymers Journal（ポリマー材料誌）
INSERT INTO sources (name, urls, parser, acquisition_mode, category, domain, country_code, relevance)
VALUES (
    'MDPI Polymers Journal',
    ARRAY['https://www.mdpi.com/rss/journal/polymers'],
    'rss',
    'auto',
    'paper',
    'mdpi.com',
    'CH',
    8
);

-- 8. MDPI Materials Journal（材料科学誌）
INSERT INTO sources (name, urls, parser, acquisition_mode, category, domain, country_code, relevance)
VALUES (
    'MDPI Materials Journal',
    ARRAY['https://www.mdpi.com/rss/journal/materials'],
    'rss',
    'auto',
    'paper',
    'mdpi.com',
    'CH',
    8
);

-- 9. Manufacturing.net（製造業情報）
INSERT INTO sources (name, urls, parser, acquisition_mode, category, domain, country_code, relevance)
VALUES (
    'Manufacturing.net',
    ARRAY['https://manufacturing.net/rss.xml'],
    'rss',
    'auto',
    'news',
    'manufacturing.net',
    'US',
    6
);

-- 10. Chemical Processing（化学工業情報）
INSERT INTO sources (name, urls, parser, acquisition_mode, category, domain, country_code, relevance)
VALUES (
    'Chemical Processing Magazine',
    ARRAY['https://chemicalprocessing.com/__rss/website-scheduled-content.xml?input=%7B%22sectionAlias%22%3A%22home%22%7D'],
    'rss',
    'auto',
    'news',
    'chemicalprocessing.com',
    'US',
    6
);

-- 11. arXiv Materials Science（材料科学分野限定）
INSERT INTO sources (name, urls, parser, acquisition_mode, category, domain, country_code)
VALUES (
    'arXiv - Materials Science Composites',
    ARRAY['https://export.arxiv.org/api/query?search_query=cat:cond-mat.mtrl-sci+AND+all:composite&max_results=30&sortBy=submittedDate&sortOrder=descending'],
    'rss',
    'auto',
    'paper',
    'arxiv.org',
    'US'
);

-- 追加完了確認用クエリ
-- SELECT name, domain, category, country_code, relevance, acquisition_mode 
-- FROM sources 
-- WHERE name LIKE '%arXiv%' OR name LIKE '%MDPI%' OR name LIKE '%AVK%' OR name LIKE '%SAMPE%' OR name LIKE '%ACMA%'
-- ORDER BY relevance DESC NULLS LAST;