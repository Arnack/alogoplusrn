import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from handlers.customer.menu.customer_orders import show_orders_list
from filters import Manager, Director
from aiogram.filters import or_f
from utils import cancel_calls_for_order
import keyboards.inline as ikb
import database as db
import texts as txt


router = Router()


@router.callback_query(or_f(Manager(), Director()), F.data.startswith('DeleteOrder:'))
async def delete_order(
        callback: CallbackQuery
):
    await callback.answer()
    order_id = callback.data.split(':')[1]
    await callback.message.edit_text(
        text=txt.accept_delete_order(),
        reply_markup=await ikb.accept_delete_order(
            order_id=order_id,
            tg_id=callback.from_user.id
        )
    )


@router.callback_query(or_f(Manager(), Director()), F.data.startswith('AcceptDeleteOrder:'))
async def delete_order(
        callback: CallbackQuery,
        state: FSMContext
):
    order_id = int(callback.data.split(':')[1])
    order = await db.get_order(order_id=order_id)

    try:
        users = await db.all_users_for_delete_order(order_id=order_id)
        await cancel_calls_for_order(order_id=order_id)
        await db.delete_order_customer(order_id=order_id)
        await callback.answer(
            text=txt.order_deleted(),
            show_alert=True
        )
        for user in users:
            try:
                await callback.bot.send_message(
                    chat_id=user,
                    text=txt.notification_for_workers(),
                    protect_content=True
                )
            except:
                pass
    except Exception as e:
        logging.exception(f'\n\n{e}')
        await callback.answer(
            text=txt.delete_order_error(),
            show_alert=True
        )
    finally:
        admins = await db.get_admins_by_customer_id(customer_id=order.customer_id)

        if callback.from_user.id in admins:
            await state.update_data(page=0)
            await show_orders_list(
                callback=callback,
                state=state
            )
            customer_admin = await db.get_customer_admin_by_tg_id(tg_id=callback.from_user.id)
            for admin in admins:
                try:
                    await callback.bot.send_message(
                        chat_id=admin,
                        text=txt.customer_deleted_order(
                            fio=customer_admin.admin_full_name,
                            order_id=order_id
                        )
                    )
                except:
                    pass
        else:
            for admin in admins:
                try:
                    await callback.bot.send_message(
                        chat_id=admin,
                        text=txt.manager_deleted_order(
                            order_id=order_id
                        )
                    )
                except:
                    pass
            await callback.message.edit_text(
                text=txt.orders_moderation(),
                reply_markup=await ikb.orders_menu()
            )

