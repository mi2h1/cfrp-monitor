-- articlesテーブル作成SQL
-- itemsテーブルと同じ構造でarticlesテーブルを作成

CREATE TABLE articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID REFERENCES sources(id),
    title TEXT,
    url TEXT,
    body TEXT,
    published_at DATE,
    src_type TEXT,
    status TEXT DEFAULT 'unread'::text,
    flagged BOOLEAN DEFAULT false,
    comments TEXT,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    last_edited_by TEXT,
    reviewer TEXT
);

-- インデックス作成
CREATE INDEX idx_articles_source_id ON articles(source_id);
CREATE INDEX idx_articles_published_at ON articles(published_at);
CREATE INDEX idx_articles_status ON articles(status);
CREATE INDEX idx_articles_flagged ON articles(flagged);
CREATE UNIQUE INDEX idx_articles_url ON articles(url);

-- RLS (Row Level Security) 設定
ALTER TABLE articles ENABLE ROW LEVEL SECURITY;

-- 認証されたユーザーのみアクセス可能
CREATE POLICY "Enable read access for authenticated users" ON articles
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Enable insert access for authenticated users" ON articles
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Enable update access for authenticated users" ON articles
    FOR UPDATE USING (auth.role() = 'authenticated');

CREATE POLICY "Enable delete access for authenticated users" ON articles
    FOR DELETE USING (auth.role() = 'authenticated');

-- コメント追加
COMMENT ON TABLE articles IS 'CFRP記事管理テーブル (旧itemsテーブル)';
COMMENT ON COLUMN articles.id IS '記事ID';
COMMENT ON COLUMN articles.source_id IS '情報源ID (sourcesテーブル参照)';
COMMENT ON COLUMN articles.title IS '記事タイトル';
COMMENT ON COLUMN articles.url IS '記事URL (ユニーク)';
COMMENT ON COLUMN articles.body IS '記事本文';
COMMENT ON COLUMN articles.published_at IS '公開日';
COMMENT ON COLUMN articles.status IS 'ステータス (unread/reviewed/flagged/archived)';
COMMENT ON COLUMN articles.flagged IS '重要フラグ';
COMMENT ON COLUMN articles.comments IS 'コメント・備考';
COMMENT ON COLUMN articles.added_at IS '追加日時';
COMMENT ON COLUMN articles.reviewed_at IS '確認日時';
COMMENT ON COLUMN articles.last_edited_by IS '最終編集者';
COMMENT ON COLUMN articles.reviewer IS '確認者';
COMMENT ON COLUMN articles.src_type IS '収集タイプ (auto/manual)';