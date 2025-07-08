-- 重複を避けた新規情報源追加SQL
-- arxiv.orgドメインの重複を回避

-- 1. 既存のarXiv CFRP papersを拡張検索に更新
UPDATE sources 
SET 
    name = 'arXiv - Enhanced Composites Search',
    urls = ARRAY['https://export.arxiv.org/api/query?search_query=all:CFRP+OR+all:"composite materials"+OR+all:GFRP+OR+all:AFRP+OR+all:"fiber reinforced"+OR+all:"metal matrix"&max_results=80&sortBy=submittedDate&sortOrder=descending']
WHERE domain = 'arxiv.org';

-- 2. ドイツ複合材料協会 AVK-TV（ヨーロッパ情報）
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

-- 3. SAMPE 先進材料学会
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

-- 4. ACMA - 米国複合材料製造業協会
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

-- 5. MDPI Journal of Composites Science（複合材料専門誌）
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

-- 6. MDPI Polymers Journal（ポリマー材料誌）
INSERT INTO sources (name, urls, parser, acquisition_mode, category, domain, country_code, relevance)
VALUES (
    'MDPI Polymers Journal',
    ARRAY['https://www.mdpi.com/rss/journal/polymers'],
    'rss',
    'auto',
    'paper',
    'mdpi.com-polymers',
    'CH',
    8
);

-- 7. MDPI Materials Journal（材料科学誌）
INSERT INTO sources (name, urls, parser, acquisition_mode, category, domain, country_code, relevance)
VALUES (
    'MDPI Materials Journal',
    ARRAY['https://www.mdpi.com/rss/journal/materials'],
    'rss',
    'auto',
    'paper',
    'mdpi.com-materials',
    'CH',
    8
);

-- 8. Manufacturing.net（製造業情報）
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

-- 9. Chemical Processing（化学工業情報）
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

-- 確認用クエリ
SELECT name, domain, category, country_code, relevance 
FROM sources 
ORDER BY relevance DESC NULLS LAST;