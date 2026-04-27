import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from decimal import Decimal

from handlers.admin.menu.customers import open_customer_info
import keyboards.inline as ikb
from filters import Admin
import database as db
import texts as txt

router = Router()


@router.callback_query(Admin(), F.data.startswith('AddPremiumWorker:'))
async def start_add_premium_worker(
    callback: CallbackQuery,
    state: FSMContext
):
    """Начать процесс закрепления исполнителя"""
    await callback.answer()
    customer_id = int(callback.data.split(':')[1])

    await state.update_data(customer_id=customer_id)
    await state.set_state('PremiumWorkerLastName')

    await callback.message.edit_text(
        text=txt.enter_premium_worker_last_name()
    )


@router.message(Admin(), F.text, StateFilter('PremiumWorkerLastName'))
async def search_worker_by_last_name(
    message: Message,
    state: FSMContext
):
    """Поиск исполнителя по фамилии"""
    last_name = message.text
    workers = await db.search_premium_workers_by_last_name(last_name)

    if not workers:
        await message.answer(
            text=txt.premium_worker_not_found(last_name)
        )
        await state.clear()
        return

    # Не сохраняем workers в state (объекты User не сериализуются в JSON)
    # ID исполнителя получим из callback_data при выборе
    await message.answer(
        text=txt.select_premium_worker(),
        reply_markup=await ikb.select_worker_from_list(workers)
    )


@router.callback_query(Admin(), F.data.startswith('SelectWorker:'))
async def select_worker(
    callback: CallbackQuery,
    state: FSMContext
):
    """Выбрать исполнителя из списка"""
    await callback.answer()
    worker_id = int(callback.data.split(':')[1])

    await state.update_data(selected_worker_id=worker_id)

    worker = await db.get_user_by_id(worker_id)
    real_data = await db.get_user_real_data_by_id(worker_id)

    await callback.message.edit_text(
        text=txt.select_bonus_type(
            last_name=real_data.last_name,
            first_name=real_data.first_name,
            middle_name=real_data.middle_name
        ),
        reply_markup=ikb.select_bonus_type()
    )


@router.callback_query(Admin(), F.data == 'BonusTypeUnconditional')
async def select_unconditional_bonus(
    callback: CallbackQuery,
    state: FSMContext
):
    """Выбрать безусловное вознаграждение"""
    await callback.answer()
    await state.update_data(bonus_type='unconditional')
    await state.set_state('EnterUnconditionalAmount')

    await callback.message.edit_text(
        text=txt.enter_unconditional_bonus_amount()
    )


@router.message(Admin(), F.text, StateFilter('EnterUnconditionalAmount'))
async def save_unconditional_amount(
    message: Message,
    state: FSMContext
):
    """Сохранить сумму безусловного вознаграждения"""
    try:
        amount = message.text.replace(',', '.')
        if not amount.replace('.', '').replace('-', '').isdigit():
            raise ValueError

        # Проверка, что сумма положительная
        if Decimal(amount) <= 0:
            raise ValueError

        data = await state.get_data()
        await state.update_data(
            conditions=[{'percent': '0,00', 'amount': amount.replace('.', ',')}]
        )

        real_data = await db.get_user_real_data_by_id(data['selected_worker_id'])

        await message.answer(
            text=txt.confirm_premium_worker(
                last_name=real_data.last_name,
                first_name=real_data.first_name,
                middle_name=real_data.middle_name,
                bonus_type='unconditional',
                amount=amount
            ),
            reply_markup=ikb.confirm_save_premium_worker(data['customer_id'])
        )
    except ValueError:
        await message.answer(
            text=txt.invalid_amount_format()
        )


@router.callback_query(Admin(), F.data == 'BonusTypeConditional')
async def select_conditional_bonus(
    callback: CallbackQuery,
    state: FSMContext
):
    """Выбрать условное вознаграждение"""
    await callback.answer()
    await state.update_data(
        bonus_type='conditional',
        conditions=[],
        current_condition_index=0
    )
    await state.set_state('EnterConditionPercent_1')

    await callback.message.edit_text(
        text=txt.enter_condition_percent(1)
    )


@router.message(Admin(), F.text, StateFilter('EnterConditionPercent_1', 'EnterConditionPercent_2',
                                              'EnterConditionPercent_3', 'EnterConditionPercent_4'))
async def save_condition_percent(
    message: Message,
    state: FSMContext
):
    """Сохранить процент для условия"""
    try:
        percent = message.text.replace(',', '.').replace('%', '').strip()
        if not percent.replace('.', '').replace('-', '').isdigit():
            raise ValueError

        percent_decimal = Decimal(percent)
        if percent_decimal < 0 or percent_decimal > 200:
            raise ValueError

        data = await state.get_data()
        condition_index = data['current_condition_index']

        await state.update_data(temp_percent=f'{percent_decimal:.2f}'.replace('.', ','))
        await state.set_state(f'EnterConditionAmount_{condition_index + 1}')

        await message.answer(
            text=txt.enter_condition_amount(condition_index + 1)
        )
    except ValueError:
        await message.answer(
            text=txt.invalid_percent_format()
        )


@router.message(Admin(), F.text, StateFilter('EnterConditionAmount_1', 'EnterConditionAmount_2',
                                              'EnterConditionAmount_3', 'EnterConditionAmount_4'))
async def save_condition_amount(
    message: Message,
    state: FSMContext
):
    """Сохранить сумму для условия"""
    try:
        amount = message.text.replace(',', '.')
        if not amount.replace('.', '').replace('-', '').isdigit():
            raise ValueError

        if Decimal(amount) <= 0:
            raise ValueError

        data = await state.get_data()
        conditions = data['conditions']
        condition_index = data['current_condition_index']

        conditions.append({
            'percent': data['temp_percent'],
            'amount': amount.replace('.', ',')
        })

        await state.update_data(
            conditions=conditions,
            current_condition_index=condition_index + 1
        )

        # Предложить добавить ещё условие или завершить
        if condition_index < 3:
            await message.answer(
                text=txt.add_more_conditions(),
                reply_markup=ikb.add_more_conditions_or_finish(data['customer_id'])
            )
        else:
            # Уже 4 условия, показываем подтверждение
            await show_confirmation(message, state, data)
    except ValueError:
        await message.answer(
            text=txt.invalid_amount_format()
        )


@router.callback_query(Admin(), F.data == 'AddMoreConditions')
async def add_more_conditions(
    callback: CallbackQuery,
    state: FSMContext
):
    """Добавить ещё одно условие"""
    await callback.answer()
    data = await state.get_data()
    new_index = data['current_condition_index']

    await state.set_state(f'EnterConditionPercent_{new_index + 1}')

    await callback.message.edit_text(
        text=txt.enter_condition_percent(new_index + 1)
    )


@router.callback_query(Admin(), F.data == 'FinishConditions')
async def finish_conditions(
    callback: CallbackQuery,
    state: FSMContext
):
    """Завершить ввод условий"""
    await callback.answer()
    data = await state.get_data()

    real_data = await db.get_user_real_data_by_id(data['selected_worker_id'])

    await callback.message.edit_text(
        text=txt.confirm_premium_worker(
            last_name=real_data.last_name,
            first_name=real_data.first_name,
            middle_name=real_data.middle_name,
            bonus_type='conditional',
            conditions=data['conditions']
        ),
        reply_markup=ikb.confirm_save_premium_worker(data['customer_id'])
    )


async def show_confirmation(message: Message, state: FSMContext, data: dict):
    """Показать подтверждение сохранения"""
    real_data = await db.get_user_real_data_by_id(data['selected_worker_id'])

    await message.answer(
        text=txt.confirm_premium_worker(
            last_name=real_data.last_name,
            first_name=real_data.first_name,
            middle_name=real_data.middle_name,
            bonus_type='conditional',
            conditions=data['conditions']
        ),
        reply_markup=ikb.confirm_save_premium_worker(data['customer_id'])
    )


@router.callback_query(Admin(), F.data == 'SavePremiumWorker')
async def save_premium_worker(
    callback: CallbackQuery,
    state: FSMContext
):
    """Сохранить закреплённого исполнителя"""
    try:
        data = await state.get_data()

        await db.set_premium_worker(
            customer_id=data['customer_id'],
            worker_id=data['selected_worker_id'],
            bonus_type=data['bonus_type'],
            conditions=data['conditions']
        )

        await callback.answer(
            text=txt.premium_worker_added(),
            show_alert=True
        )

        await open_customer_info(
            callback=callback,
            customer_id=data['customer_id']
        )
    except Exception as e:
        await callback.answer(
            text=txt.premium_worker_add_error(),
            show_alert=True
        )
        logging.exception(f'\n\n{e}')
    finally:
        await state.clear()
