from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

import database as db
from filters import Admin
import keyboards.inline as ikb
import texts as txt


router = Router()
router.message.filter(Admin())
router.callback_query.filter(Admin())


@router.callback_query(F.data.startswith('SetTravelCompensation:'))
async def set_travel_compensation(
        callback: CallbackQuery,
        state: FSMContext
):
    """Установка суммы компенсации Платформы за проезд"""
    await callback.answer()
    customer_id = int(callback.data.split(':')[1])

    await callback.message.edit_text(
        text=txt.set_travel_compensation_request()
    )

    await state.update_data(customer_id=customer_id)
    await state.set_state('SetTravelCompensation')


@router.message(F.text, StateFilter('SetTravelCompensation'))
async def save_travel_compensation(
        message: Message,
        state: FSMContext
):
    """Сохранение суммы компенсации"""
    data = await state.get_data()
    customer_id = data['customer_id']

    try:
        # Проверка на положительное число
        amount = int(message.text)
        if amount <= 0:
            await message.answer(text=txt.travel_compensation_error())
            return

        # Сохранение в БД
        await db.set_travel_compensation(
            customer_id=customer_id,
            amount=amount
        )

        await message.answer(
            text=txt.travel_compensation_saved(amount=amount)
        )

        # Возврат к карточке заказчика
        from handlers.admin.menu.customers import open_customer_info
        from aiogram.types import CallbackQuery as FakeCallback

        # Создаем фейковый callback для вызова функции
        class FakeCallbackQuery:
            def __init__(self, msg):
                self.message = msg

        fake_callback = FakeCallbackQuery(message)
        await open_customer_info(
            callback=fake_callback,
            customer_id=customer_id
        )

    except ValueError:
        await message.answer(text=txt.travel_compensation_error())
    finally:
        await state.clear()
