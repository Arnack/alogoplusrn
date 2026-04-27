"""Совместимость со старыми импортами utils.loggers.payments."""

from . import write_accountant_op_log, write_worker_op_log

__all__ = ['write_accountant_op_log', 'write_worker_op_log']
