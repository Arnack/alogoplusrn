"""
Конфигурация для Max Worker Bot
Использует общий config_reader проекта
"""
import sys
import os

# Добавляем родительскую директорию для импорта config_reader
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_reader import config

# Экспортируем config для использования в модулях Max бота
__all__ = ['config']
