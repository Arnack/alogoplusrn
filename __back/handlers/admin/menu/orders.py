from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import or_f
import logging

from filters import Admin, Director
import keyboards.inline as ikb
import database as db


router = Router()
router.message.filter(or_f(Admin(), Director()))
router.callback_query.filter(or_f(Admin(), Director()))


@router.callback_query(F.data == 'AdminOrdersMenu')
@router.message(F.text == '📦 Заявки')
async def admin_orders_main_menu(
        event: Message | CallbackQuery,
        state: FSMContext
):
    """Главное меню управления заявками от имени заказчиков"""
    await state.clear()
    
    text = (
        "📋 <b>Управление заявками</b>\n\n"
        "Вы можете размещать и закрывать заявки от имени получателей услуг.\n"
        "Выберите город для продолжения."
    )
    
    if isinstance(event, Message):
        await event.answer(
            text=text,
            reply_markup=ikb.admin_orders_menu()
        )
    else:
        await event.answer()
        await event.message.edit_text(
            text=text,
            reply_markup=ikb.admin_orders_menu()
        )


@router.callback_query(F.data == 'AdminOrdersSelectCity')
async def select_city_for_orders(
        callback: CallbackQuery
):
    """Выбор города для работы с заявками"""
    await callback.answer()
    
    text = (
        "🌆 <b>Выбор города</b>\n\n"
        "Выберите город для просмотра и размещения заявок:"
    )
    
    await callback.message.edit_text(
        text=text,
        reply_markup=await ikb.cities_for_orders()
    )


@router.callback_query(F.data.startswith('AdminOrderCity:'))
async def show_customers_list(
        callback: CallbackQuery,
        state: FSMContext
):
    """Показать список заказчиков города"""
    await callback.answer()
    city = callback.data.split(':')[1]

    # Сохраняем город в состояние
    await state.update_data(selected_city=city)

    text = (
        f"🌆 <b>Город: {city}</b>\n\n"
        "Выберите получателя услуг:"
    )

    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=await ikb.customers_list_for_orders(city=city)
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith('AdminOrderCustomer:'))
async def show_customer_panel_for_admin(
        callback: CallbackQuery,
        state: FSMContext
):
    """Панель управления от имени выбранного заказчика"""
    await callback.answer()
    
    parts = callback.data.split(':')
    customer_id = int(parts[1])
    city = parts[2]
    
    # Проверяем есть ли представители у заказчика
    customer_admins = await db.get_admins_by_customer_id(customer_id=customer_id)
    if not customer_admins:
        await callback.message.edit_text(
            text="У данного получателя услуг нет представителей"
        )
        return

    # Берем первого админа для работы с заявками
    customer_admin_tg_id = customer_admins[0]

    # Сохраняем данные в состояние
    await state.update_data(
        admin_as_customer=True,
        admin_customer_id=customer_id,
        admin_city=city,
        admin_as_customer_id=customer_admin_tg_id
    )

    # Сразу показываем меню управления заявками (как у заказчиков)
    import texts as txt
    await callback.message.edit_text(
        text=txt.orders(),
        reply_markup=ikb.order_management()
    )


@router.callback_query(F.data == 'AllCustomerOrders')
async def admin_open_customer_orders_list(
        callback: CallbackQuery,
        state: FSMContext
):
    """Показать список заявок заказчика (для админа)"""
    await callback.answer()
    data = await state.get_data()
    customer_admin_tg_id = data.get('admin_as_customer_id')

    if not customer_admin_tg_id:
        await callback.answer("Ошибка: получатель услуг не выбран", show_alert=True)
        return

    # Получаем заявки от имени заказчика
    orders = await db.get_customer_orders(admin=customer_admin_tg_id)

    if not orders:
        import texts as txt
        await callback.message.edit_text(
            text=txt.no_orders_customer(),
            reply_markup=ikb.back_to_order_management_menu()
        )
        return

    # Вызываем функцию показа заявок
    from handlers.customer.menu.customer_orders import open_customer_order

    await state.update_data(page=0)
    await open_customer_order(
        callback=callback,
        state=state,
        page=0,
        admin_id=customer_admin_tg_id
    )


@router.callback_query(F.data == 'BackToOrderManagement')
async def back_to_order_management(
        callback: CallbackQuery
):
    """Вернуться к меню управления заказами"""
    await callback.answer()
    import texts as txt
    await callback.message.edit_text(
        text=txt.orders(),
        reply_markup=ikb.order_management()
    )
