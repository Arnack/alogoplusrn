-- Migration: add card_snapshot column to worker_acts
-- Date: 2026-04-01
-- Purpose: П.10 ТЗ - фиксация карты на момент подписания акта

ALTER TABLE worker_acts
    ADD COLUMN IF NOT EXISTS card_snapshot VARCHAR(16);

COMMENT ON COLUMN worker_acts.card_snapshot IS 'Номер карты работника на момент подписания акта (для фиксации при выплате)';
