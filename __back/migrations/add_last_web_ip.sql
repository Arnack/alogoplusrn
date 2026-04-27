-- Миграция: добавление поля last_web_ip для исполнителей
-- Дата: 2026-03-26

ALTER TABLE users ADD COLUMN IF NOT EXISTS last_web_ip VARCHAR(45);
