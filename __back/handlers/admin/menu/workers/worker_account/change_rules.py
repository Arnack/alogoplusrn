from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
import logging

from handlers.admin.menu.workers.worker_account.open_account_menu import open_worker_account_menu
import keyboards.inline as ikb
from filters import Admin, Director
from aiogram.filters import or_f
import database as db
import texts as txt


router = Router()


@router.callback_query(or_f(Admin(), Director()), F.data == 'BotRules')
async def change_rules_menu(
        callback: CallbackQuery
):
    await callback.answer()
    await callback.message.edit_text(
        text=txt.request_choose_category(),
        reply_markup=ikb.choose_rules_for()
    )


@router.callback_query(or_f(Admin(), Director()), F.data.startswith('RulesFor:'))
async def get_rules_for(
        callback: CallbackQuery
):
    await callback.answer()
    await callback.message.edit_text(
        text=txt.request_choose_action(),
        reply_markup=ikb.admin_rules_actions(
            rules_for=callback.data.split(':')[1]
        )
    )


@router.callback_query(or_f(Admin(), Director()), F.data.startswith('ShowRules:'))
async def show_rules_for(
        callback: CallbackQuery
):
    rules_for = callback.data.split(':')[1]
    rules = await db.get_rules(
        rules_for=rules_for
    )
    if rules:
        await callback.answer()
        await callback.message.edit_text(
            text=txt.show_rules_text(
                text=rules.rules,
                date=rules.date
            ),
            reply_markup=ikb.back_to_rules_menu(
                rules_for=rules_for
            )
        )
    else:
        await callback.answer(
            text=txt.no_rules(),
            show_alert=True
        )


@router.callback_query(or_f(Admin(), Director()), F.data.startswith('UpdateRules:'))
async def update_rules_for(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    rules_for = callback.data.split(':')[1]
    await callback.message.edit_text(
        text=txt.request_new_rules(
            rules_for=rules_for
        )
    )
    await state.update_data(
        RulesFor=rules_for
    )
    await state.set_state(
        'RequestNewRules'
    )


@router.message(or_f(Admin(), Director()), F.text, StateFilter('RequestNewRules'))
async def get_new_rules(
        message: Message,
        state: FSMContext
):
    await state.set_state(None)
    data = await state.get_data()
    await message.answer(
        text=txt.confirmation_update_rules(
            rules_for=data['RulesFor']
        ),
        reply_markup=ikb.confirmation_update_rules(
            rules_for=data['RulesFor']
        )
    )
    await state.update_data(
        Rules=message.html_text
    )


@router.callback_query(or_f(Admin(), Director()), F.data.startswith('ConfirmUpdateRules:'))
async def confirm_update_rules(
        callback: CallbackQuery,
        state: FSMContext
):
    data = await state.get_data()
    try:
        await db.set_or_update_rules(
            new_rules=data['Rules'],
            rules_for=data['RulesFor']
        )
        await callback.message.edit_text(
            text=txt.rules_updated(
                rules_for=data['RulesFor']
            ),
            reply_markup=ikb.notification_for_update_rules(
                notification_for=data['RulesFor']
            )
        )
    except Exception as e:
        logging.exception(f'\n\n{e}')
        await callback.message.edit_text(
            text=txt.update_rules_error(
                rules_for=data['RulesFor']
            )
        )
    finally:
        await state.clear()


@router.callback_query(or_f(Admin(), Director()), F.data.startswith('RulesSendNotification:'))
async def start_rules_notification(
        callback: CallbackQuery
):
    try:
        if callback.data.split(':')[1] == 'workers':
            users = await db.get_workers_tg_id()
        else:
            users = await db.get_foremen_tg_id()

        await callback.answer(
            text=txt.rules_notification_start(),
            show_alert=True
        )
        for tg_id in users:
            try:
                await callback.bot.send_message(
                    chat_id=tg_id,
                    text=txt.rules_notification()
                )
            except:
                pass
    finally:
        await open_worker_account_menu(
            callback=callback
        )

