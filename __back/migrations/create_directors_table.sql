-- Миграция: Создание таблицы directors
-- Дата: 2026-02-25
-- Описание: Добавление новой роли "Директор" с полем должности

CREATE TABLE IF NOT EXISTS directors (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(50) NOT NULL,
    position VARCHAR(50) NOT NULL,
    tg_id BIGINT NOT NULL
);

-- Создать индекс для быстрого поиска по tg_id
CREATE INDEX IF NOT EXISTS idx_directors_tg_id ON directors(tg_id);

-- Комментарии к таблице
COMMENT ON TABLE directors IS 'Директора платформы с расширенными правами';
COMMENT ON COLUMN directors.full_name IS 'ФИО директора';
COMMENT ON COLUMN directors.position IS 'Должность директора (используется в подписях документов)';
COMMENT ON COLUMN directors.tg_id IS 'Telegram ID директора';
