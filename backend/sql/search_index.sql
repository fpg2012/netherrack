-- 可选：pg_trgm 索引（需要 postgresql-contrib）
-- 数据量小时顺序扫描也够；帖子多了再执行。
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX IF NOT EXISTS ix_posts_body_trgm
    ON posts USING gin (body_html gin_trgm_ops);
