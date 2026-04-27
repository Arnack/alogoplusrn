"""
conftest.py — stub all dependencies not installed in the test venv.
maxapi is installed from the server tarball; aiogram and SQLAlchemy are stubbed.
"""

import sys
import types
from unittest.mock import MagicMock


class _AutoPkg(types.ModuleType):
    """Module stub: attribute/sub-module access always succeeds (returns MagicMock or sub-stub)."""

    def __init__(self, name):
        super().__init__(name)
        self.__path__ = []   # marks it as a package
        self.__all__ = []

    def __getattr__(self, name):
        full = f'{self.__name__}.{name}'
        if full not in sys.modules:
            sub = _AutoPkg(full)
            sys.modules[full] = sub
        obj = sys.modules[full]
        object.__setattr__(self, name, obj)
        return obj


def _stub(*names):
    for name in names:
        if name not in sys.modules:
            sys.modules[name] = _AutoPkg(name)


# Stub every aiogram sub-path that keyboards/handlers transitively import
_stub(
    'aiogram',
    'aiogram.types',
    'aiogram.filters',
    'aiogram.fsm',
    'aiogram.fsm.context',
    'aiogram.fsm.state',
    'aiogram.utils',
    'aiogram.utils.keyboard',
    'aiogram.exceptions',
    'aiogram.dispatcher',
    'aiogram.dispatcher.middlewares',
)

# aiogram.filters.callback_data — CallbackData is used as a base class,
# so it must be a real Python class, not a module stub.
class _CallbackData:
    def __init_subclass__(cls, prefix='', **kwargs):
        super().__init_subclass__(**kwargs)

_cbd_mod = _AutoPkg('aiogram.filters.callback_data')
_cbd_mod.CallbackData = _CallbackData
sys.modules['aiogram.filters.callback_data'] = _cbd_mod

# Expose via aiogram.filters as well
sys.modules['aiogram.filters'].CallbackData = _CallbackData
