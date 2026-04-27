"""
Скрипт для проверки доступных типов кнопок в maxapi
"""
import sys

try:
    # Пробуем разные варианты импорта
    print("Проверка доступных кнопок в maxapi...\n")

    # Вариант 1: из maxapi.types.attachments.buttons
    try:
        from maxapi.types.attachments.buttons import (
            CallbackButton,
            LinkButton,
            MessageButton
        )
        print("✓ CallbackButton, LinkButton, MessageButton импортированы из maxapi.types.attachments.buttons")
    except ImportError as e:
        print(f"✗ Ошибка импорта из maxapi.types.attachments.buttons: {e}")

    # Проверяем RequestContact
    try:
        from maxapi.types.attachments.buttons import RequestContact
        print("✓ RequestContact доступен")
    except ImportError:
        print("✗ RequestContact НЕ доступен")

    # Проверяем RequestContactButton
    try:
        from maxapi.types.attachments.buttons import RequestContactButton
        print("✓ RequestContactButton доступен")
    except ImportError:
        print("✗ RequestContactButton НЕ доступен")

    # Проверяем из maxapi.types
    try:
        from maxapi.types import RequestContactButton
        print("✓ RequestContactButton доступен из maxapi.types")
    except ImportError:
        print("✗ RequestContactButton НЕ доступен из maxapi.types")

    # Пробуем вывести все доступные кнопки
    print("\nДоступные кнопки в maxapi.types.attachments.buttons:")
    try:
        import maxapi.types.attachments.buttons as buttons_module
        button_types = [name for name in dir(buttons_module) if not name.startswith('_')]
        for btn in button_types:
            print(f"  - {btn}")
    except Exception as e:
        print(f"Ошибка: {e}")

except Exception as e:
    print(f"Общая ошибка: {e}")
    import traceback
    traceback.print_exc()
