import html as html_module
import re


def no_rules() -> str:
    return f'ℹ️ Правила еще не добавлены'


def show_rules_text(
        text: str,
        date: str
) -> str:
    return f'<blockquote>{text}\n\n' \
           f'<b>Актуально с {date}</b></blockquote>'


# Плейсхолдеры для безопасного разрешения HTML-тегов (экранируем всё, кроме b/strong/i/em)
_ALLOWED_TAGS = [
    ('<b>', '\x00B1\x00'), ('</b>', '\x00B2\x00'),
    ('<strong>', '\x00S1\x00'), ('</strong>', '\x00S2\x00'),
    ('<i>', '\x00I1\x00'), ('</i>', '\x00I2\x00'),
    ('<em>', '\x00E1\x00'), ('</em>', '\x00E2\x00'),
]


def _restore_allowed_tags(s: str) -> str:
    for tag, ph in _ALLOWED_TAGS:
        s = s.replace(ph, tag)
    return s


def _hide_allowed_tags(s: str) -> str:
    for tag, ph in _ALLOWED_TAGS:
        s = s.replace(tag, ph)
    return s


def show_rules_text_for_web_panel(text: str, date: str) -> str:
    """Веб-панель: крупнее, абзацы, без сплошного blockquote (удобнее при слабом зрении)."""
    raw = (text or '').strip()
    if not raw:
        return f'<div class="panel-rich-text"><p class="panel-rich-p">{html_module.escape(no_rules())}</p></div>'
    chunks = [c.strip() for c in re.split(r'\n{2,}', raw) if c.strip()]
    if len(chunks) == 1:
        chunks = [ln.strip() for ln in raw.split('\n') if ln.strip()]
    paras = []
    for ch in chunks:
        safe = _hide_allowed_tags(ch)
        inner = _restore_allowed_tags(html_module.escape(safe)).replace('\n', '<br>')
        paras.append(f'<p class="panel-rich-p">{inner}</p>')
    d = html_module.escape(date or '—')
    return (
        '<div class="panel-rich-text panel-rich-text--rules">'
        + ''.join(paras)
        + f'<p class="panel-rich-meta">Актуально с <strong>{d}</strong></p></div>'
    )


def request_date_all_formats() -> str:
    return '🗓️ Введите дату в формате ДД.ММ или ДД.ММ.ГГ или ДД.ММ.ГГГГ:'


def all_format_date_error() -> str:
    return '❗Неверный формат даты. Введите дату в формате ДД.ММ или ДД.ММ.ГГ или ДД.ММ.ГГГГ:'
