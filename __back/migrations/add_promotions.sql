-- Миграция: добавление таблиц для модуля «Акция»
-- Дата: 2026-03-26

CREATE TABLE IF NOT EXISTS promotions (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    type VARCHAR(10) NOT NULL,           -- 'streak' / 'period'
    name VARCHAR(100) NOT NULL,
    description TEXT,
    n_orders INTEGER NOT NULL,           -- N (streak) / K (period)
    period_days INTEGER,                 -- D (только для period)
    bonus_amount INTEGER NOT NULL,       -- сумма за 1 заявку (₽)
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    city VARCHAR(25) NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_promotions_customer_id ON promotions(customer_id);

CREATE TABLE IF NOT EXISTS promotion_participations (
    id SERIAL PRIMARY KEY,
    promotion_id INTEGER NOT NULL REFERENCES promotions(id) ON DELETE CASCADE,
    worker_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    current_streak INTEGER NOT NULL DEFAULT 0,
    period_start_at TIMESTAMP,
    period_completed INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(15) NOT NULL DEFAULT 'active',
    cycles_completed INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS ix_promotion_participations_promotion_id ON promotion_participations(promotion_id);
CREATE INDEX IF NOT EXISTS ix_promotion_participations_worker_id ON promotion_participations(worker_id);

CREATE TABLE IF NOT EXISTS promotion_bonuses (
    id SERIAL PRIMARY KEY,
    participation_id INTEGER NOT NULL REFERENCES promotion_participations(id) ON DELETE CASCADE,
    worker_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    promotion_name VARCHAR(100) NOT NULL,
    amount INTEGER NOT NULL,
    accrued_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_promotion_bonuses_worker_id ON promotion_bonuses(worker_id);
