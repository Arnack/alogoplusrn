ALTER TABLE users
ADD COLUMN IF NOT EXISTS max_chat_id BIGINT NOT NULL DEFAULT 0;

UPDATE users
SET max_chat_id = 0
WHERE max_chat_id IS NULL;

CREATE INDEX IF NOT EXISTS ix_users_max_chat_id
ON users (max_chat_id);
