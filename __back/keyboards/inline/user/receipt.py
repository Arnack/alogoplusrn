"""Клавиатуры для флоу чека из «Мой налог» (п.9 ТЗ)."""
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import WebAppInfo


def receipt_copy_keyboard(service_name: str, inn: str, amount: str) -> InlineKeyboardMarkup:
    """
    Клавиатура с кнопками копирования названия услуги и ИНН для чека.

    Args:
        service_name: Название услуги (до 256 символов)
        inn: ИНН юридического лица
    """
    builder = InlineKeyboardBuilder()

    # Кнопка копирования названия услуги
    builder.row(
        InlineKeyboardButton(
            text='📋 Скопировать название услуги',
            callback_data=f'CopyServiceName:{service_name}',
        )
    )

    builder.row(
        InlineKeyboardButton(
            text='💰 Скопировать сумму',
            callback_data=f'CopyReceiptAmount:{amount}',
        )
    )

    # Кнопка копирования ИНН
    builder.row(
        InlineKeyboardButton(
            text='📋 Скопировать ИНН',
            callback_data=f'CopyInn:{inn}',
        )
    )

    builder.row(
        InlineKeyboardButton(
            text='📎 Отправить скриншот',
            callback_data='ReceiptScreenshot',
        ),
        InlineKeyboardButton(
            text='🔗 Отправить ссылку',
            callback_data='ReceiptSent',
        )
    )

    return builder.as_markup()


def receipt_instruction_back_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой возврата к инструкции."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text='🔄 Показать инструкцию',
            callback_data='ShowReceiptInstruction',
        )
    )
    return builder.as_markup()
