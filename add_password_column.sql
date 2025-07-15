-- usersテーブルにパスワードカラムを追加
ALTER TABLE users ADD COLUMN password_hash TEXT;

-- 既存ユーザーにデフォルトパスワードを設定（実際の運用では個別に設定）
UPDATE users SET password_hash = 'default123' WHERE password_hash IS NULL;

-- パスワードを必須にする（NULL不可にする）
ALTER TABLE users ALTER COLUMN password_hash SET NOT NULL;