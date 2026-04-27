"""
Скрипт генерации Apple Touch иконок.

Сначала пробует cairosvg (точный рендеринг SVG, нужен libcairo).
Если недоступен — генерирует брендовую иконку через Pillow (fallback).

Запускать из корня проекта: python scripts/generate_apple_icons.py
На Linux-сервере: apt-get install libcairo2 && pip install cairosvg && python scripts/generate_apple_icons.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SVG_PATH = os.path.join(ROOT, 'frontend', 'static', 'botlogo.svg')
ICONS_DIR = os.path.join(ROOT, 'frontend', 'icons')


def _make_icons_dir():
    os.makedirs(ICONS_DIR, exist_ok=True)


def generate_with_cairosvg():
    import cairosvg
    _make_icons_dir()
    for size, name in [(180, 'apple-touch-icon.png'), (512, 'apple-touch-icon-512.png')]:
        out = os.path.join(ICONS_DIR, name)
        cairosvg.svg2png(url=SVG_PATH, write_to=out, output_width=size, output_height=size)
        print(f'[cairosvg] {out}')


def generate_with_pillow():
    """Генерирует брендовую иконку через Pillow (без SVG-рендеринга)."""
    from PIL import Image, ImageDraw, ImageFont
    _make_icons_dir()

    # Цвета платформы (из CSS-переменных index.html)
    BG_COLOR = (0, 122, 255)       # --accent: #007aff
    TEXT_COLOR = (255, 255, 255)   # белый

    for size, name in [(180, 'apple-touch-icon.png'), (512, 'apple-touch-icon-512.png')]:
        img = Image.new('RGB', (size, size), color=BG_COLOR)
        draw = ImageDraw.Draw(img)

        # Скруглённые углы через маску
        radius = size // 5
        mask = Image.new('L', (size, size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
        bg = Image.new('RGB', (size, size), (255, 255, 255))
        bg.paste(img, mask=mask)
        img = bg

        # Надпись AP (Algoritm Plus)
        draw = ImageDraw.Draw(img)
        font_size = size // 3
        try:
            font = ImageFont.truetype('arial.ttf', font_size)
        except Exception:
            font = ImageFont.load_default(size=font_size)

        text = 'AP'
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = (size - tw) // 2 - bbox[0]
        y = (size - th) // 2 - bbox[1]
        draw.text((x, y), text, fill=BG_COLOR, font=font)

        out = os.path.join(ICONS_DIR, name)
        img.save(out, 'PNG')
        print(f'[pillow] {out}')


def main():
    try:
        import cairosvg  # noqa
        print('Используем cairosvg...')
        generate_with_cairosvg()
    except (ImportError, OSError):
        print('cairosvg недоступен, используем Pillow (fallback)...')
        try:
            generate_with_pillow()
        except ImportError:
            print('ОШИБКА: установите Pillow: pip install pillow')
            sys.exit(1)
    print('Готово!')


if __name__ == '__main__':
    main()
