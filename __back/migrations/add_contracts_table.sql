CREATE TABLE IF NOT EXISTS contracts (
    id          SERIAL PRIMARY KEY,
    number      VARCHAR(20) UNIQUE NOT NULL,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    legal_entity_id INTEGER NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    signed_at   TIMESTAMP,
    sign_tg_id  BIGINT,
    is_archived BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_contracts_user_id ON contracts(user_id);
