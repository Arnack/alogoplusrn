-- Migration: add file_path column to contracts
-- Date: 2026-04-01
-- Purpose: П.11 ТЗ - хранение пути к PDF договору

ALTER TABLE contracts
    ADD COLUMN IF NOT EXISTS file_path VARCHAR(255);

COMMENT ON COLUMN contracts.file_path IS 'Путь к файлу PDF договора в хранилище';
