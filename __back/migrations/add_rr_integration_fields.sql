-- Миграция: добавление полей для интеграции с новым API РР (Рабочие Руки)
-- Дата: 2026-03-14

-- 1. Новые поля в таблице users
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS passport_data_complete BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS smz_status VARCHAR(20),
    ADD COLUMN IF NOT EXISTS gender VARCHAR(1);

-- 2. Паспортные данные в таблице dataForSecurity
ALTER TABLE "dataForSecurity"
    ADD COLUMN IF NOT EXISTS passport_series VARCHAR(4),
    ADD COLUMN IF NOT EXISTS passport_number VARCHAR(6),
    ADD COLUMN IF NOT EXISTS passport_issue_date VARCHAR(10),
    ADD COLUMN IF NOT EXISTS passport_department_code VARCHAR(7),
    ADD COLUMN IF NOT EXISTS passport_issued_by VARCHAR(200);

-- 3. Поля РР-заявки в таблице orders
ALTER TABLE orders
    ADD COLUMN IF NOT EXISTS rr_order_id INTEGER,
    ADD COLUMN IF NOT EXISTS rr_shift_id VARCHAR(50),
    ADD COLUMN IF NOT EXISTS legal_entity_id INTEGER;

-- 4. Флаг исполнителя РР в order_workers
ALTER TABLE order_workers
    ADD COLUMN IF NOT EXISTS is_rr_worker BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS rr_worker_inn VARCHAR(12);

-- 5. Поля штрафов/премий/рейтинга в order_workers_archive
ALTER TABLE order_workers_archive
    ADD COLUMN IF NOT EXISTS is_rr_worker BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS penalty_amount INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS bonus_amount INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS rating_deduction INTEGER DEFAULT 0;
