-- Migration: add WorkerAct, Receipt tables; add order_id to contracts
-- Date: 2026-03-28

-- 1. Add order_id column to contracts (nullable FK to orders)
ALTER TABLE contracts
    ADD COLUMN IF NOT EXISTS order_id INTEGER REFERENCES orders(id) ON DELETE SET NULL;

-- 2. Create worker_acts table
CREATE TABLE IF NOT EXISTS worker_acts (
    id            SERIAL PRIMARY KEY,
    order_id      INTEGER REFERENCES orders(id) ON DELETE SET NULL,
    worker_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    legal_entity_id INTEGER NOT NULL,
    amount        VARCHAR(20) NOT NULL,
    date          VARCHAR(15) NOT NULL,
    status        VARCHAR(30) NOT NULL DEFAULT 'pending',
    created_at    TIMESTAMP NOT NULL DEFAULT NOW(),
    signed_at     TIMESTAMP,
    file_path     VARCHAR(255)
);

-- 3. Create receipts table
CREATE TABLE IF NOT EXISTS receipts (
    id          SERIAL PRIMARY KEY,
    act_id      INTEGER NOT NULL REFERENCES worker_acts(id) ON DELETE CASCADE,
    worker_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    url         TEXT NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    file_path   VARCHAR(255)
);
