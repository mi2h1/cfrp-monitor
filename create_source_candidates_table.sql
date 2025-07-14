-- 情報源候補管理テーブルの作成
-- 週次探索で発見された候補を管理し、承認・保留・却下の workflow を提供

-- 1. source_candidates テーブルの作成
CREATE TABLE IF NOT EXISTS source_candidates (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    
    -- 基本情報
    name TEXT NOT NULL,
    domain TEXT NOT NULL,
    urls TEXT[] NOT NULL,  -- 候補のRSSフィードURL配列
    site_url TEXT,         -- 元のサイトURL
    
    -- 分類・メタデータ
    category TEXT DEFAULT 'unknown',           -- manufacturer, media, academic, etc.
    language TEXT DEFAULT 'unknown',           -- japanese, german, chinese, etc.
    country_code TEXT DEFAULT 'unknown',       -- JP, DE, CN, KR, etc.
    
    -- 品質評価
    relevance_score DECIMAL(3,2) DEFAULT 0.0,  -- 0.0-1.0 関連度スコア
    discovery_method TEXT DEFAULT 'unknown',    -- weekly_source_discovery, weekly_multilingual_discovery, manual
    
    -- 承認ワークフロー
    status TEXT DEFAULT 'pending',              -- pending, approved, rejected, on_hold
    reviewed_at TIMESTAMP WITH TIME ZONE,
    reviewer_notes TEXT,
    
    -- 探索情報
    discovered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    discovery_task_id UUID,                    -- task_logs テーブルとの関連
    
    -- 追加情報（JSON形式）
    metadata JSONB DEFAULT '{}'::jsonb,        -- RSS検証結果、エラー情報など
    
    -- 制約
    CONSTRAINT source_candidates_status_check CHECK (status IN ('pending', 'approved', 'rejected', 'on_hold')),
    CONSTRAINT source_candidates_relevance_check CHECK (relevance_score >= 0.0 AND relevance_score <= 1.0),
    CONSTRAINT source_candidates_discovery_method_check CHECK (discovery_method IN ('weekly_source_discovery', 'weekly_multilingual_discovery', 'manual', 'unknown')),
    
    -- 重複防止（同じドメインの候補は1つまで）
    UNIQUE(domain)
);

-- 2. インデックスの作成
CREATE INDEX IF NOT EXISTS idx_source_candidates_status ON source_candidates(status);
CREATE INDEX IF NOT EXISTS idx_source_candidates_discovered_at ON source_candidates(discovered_at DESC);
CREATE INDEX IF NOT EXISTS idx_source_candidates_relevance ON source_candidates(relevance_score DESC);
CREATE INDEX IF NOT EXISTS idx_source_candidates_language ON source_candidates(language);
CREATE INDEX IF NOT EXISTS idx_source_candidates_discovery_method ON source_candidates(discovery_method);

-- 3. RLSを有効化
ALTER TABLE source_candidates ENABLE ROW LEVEL SECURITY;

-- 4. RLSポリシーの作成
-- 既存のポリシーがある場合は削除してから作成
DROP POLICY IF EXISTS "source_candidates_read_all" ON source_candidates;
DROP POLICY IF EXISTS "source_candidates_insert_anon" ON source_candidates;
DROP POLICY IF EXISTS "source_candidates_update_auth" ON source_candidates;

-- 読み取りは全員可能
CREATE POLICY "source_candidates_read_all" ON source_candidates 
    FOR SELECT USING (true);

-- 挿入はanon権限でも可能（スクリプトから実行するため）
CREATE POLICY "source_candidates_insert_anon" ON source_candidates 
    FOR INSERT WITH CHECK (true);

-- 更新は管理者のみ（承認・却下のため）
CREATE POLICY "source_candidates_update_auth" ON source_candidates 
    FOR UPDATE USING (true) WITH CHECK (true);

-- 5. コメントの追加
COMMENT ON TABLE source_candidates IS '週次探索で発見された情報源候補の管理';
COMMENT ON COLUMN source_candidates.name IS '情報源名（サイト名またはドメイン名）';
COMMENT ON COLUMN source_candidates.domain IS 'ドメイン名（重複チェック用）';
COMMENT ON COLUMN source_candidates.urls IS 'RSSフィードURL配列';
COMMENT ON COLUMN source_candidates.site_url IS '元のサイトURL';
COMMENT ON COLUMN source_candidates.status IS '承認ステータス（pending/approved/rejected/on_hold）';
COMMENT ON COLUMN source_candidates.relevance_score IS '関連度スコア（0.0-1.0）';
COMMENT ON COLUMN source_candidates.discovery_method IS '発見方法（weekly_source_discovery/weekly_multilingual_discovery/manual）';
COMMENT ON COLUMN source_candidates.metadata IS '追加情報（RSS検証結果、エラー情報など）';

-- 6. 候補の自動削除用関数（オプション）
-- 30日以上経過した却下済み候補を削除
CREATE OR REPLACE FUNCTION cleanup_old_rejected_candidates()
RETURNS integer AS $$
DECLARE
    deleted_count integer;
BEGIN
    DELETE FROM source_candidates 
    WHERE status = 'rejected' 
    AND reviewed_at < NOW() - INTERVAL '30 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- 7. テスト用のサンプルデータ（既存データがある場合はスキップ）
INSERT INTO source_candidates (
    name,
    domain,
    urls,
    site_url,
    category,
    language,
    country_code,
    relevance_score,
    discovery_method,
    metadata
) 
SELECT 
    'CompositesWorld Japan',
    'compositesworld.jp',
    ARRAY['https://compositesworld.jp/rss.xml'],
    'https://compositesworld.jp',
    'media',
    'japanese',
    'JP',
    0.85,
    'weekly_multilingual_discovery',
    '{"rss_validated": true, "feed_entries": 25, "last_updated": "2025-07-14"}'::jsonb
WHERE NOT EXISTS (
    SELECT 1 FROM source_candidates WHERE domain = 'compositesworld.jp'
);

INSERT INTO source_candidates (
    name,
    domain,
    urls,
    site_url,
    category,
    language,
    country_code,
    relevance_score,
    discovery_method,
    metadata
) 
SELECT 
    'Toray Carbon Fiber News',
    'toray.com',
    ARRAY['https://toray.com/news/rss.xml'],
    'https://toray.com/news',
    'manufacturer',
    'japanese',
    'JP',
    0.92,
    'weekly_source_discovery',
    '{"rss_validated": true, "feed_entries": 12, "industry_relevance": "high"}'::jsonb
WHERE NOT EXISTS (
    SELECT 1 FROM source_candidates WHERE domain = 'toray.com'
);

-- 8. 確認
SELECT 
    name,
    domain,
    status,
    relevance_score,
    discovery_method,
    discovered_at
FROM source_candidates 
ORDER BY discovered_at DESC;