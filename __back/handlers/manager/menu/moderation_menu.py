from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from datetime import datetime
import logging
from database import (
    Order,
    async_session
)
from sqlalchemy import select, func, delete, update
from utils import (
    schedule_customer_order_notifications,
    convert_pdf_pages_to_byte_streams,
    get_day_of_week_by_date,
    schedule_call_campaign
)
import keyboards.inline as ikb
from utils import PdfGenerator
from filters import Manager, Director
from aiogram.filters import or_f, StateFilter
import database as db
import texts as txt
from utils.refuse_assigned_worker import strip_html_plain


router = Router()


async def open_moderation_applications(
        callback: CallbackQuery,
        state: FSMContext
) -> None:
    data = await state.get_data()
    count = await db.get_orders_count_for_applications_moderation()

    if callback.data == 'BackToModerationApplications':
        try:
            page = data['moder_order_page']
            index = data['index']
        except KeyError:
            page = 1
            index = 5
    else:
        page = 1
        index = 5

    if count > 0:
        await state.update_data(
            moder_order_page=page,
            index=index
        )
        await callback.message.edit_text(
            text=txt.order_applications_info(),
            reply_markup=await ikb.orders_info(
                index=index,
                page=page
            )
        )
    else:
        await callback.message.edit_text(
            text=txt.no_orders_in_progress(),
            reply_markup=ikb.back_to_moderation_menu()
        )


@router.callback_query(or_f(Manager(), Director()), F.data == 'BackToModerationMenu')
@router.message(or_f(Manager(), Director()), F.text == '🧾 Модерация заявок')
async def orders_moderation(
        event: Message | CallbackQuery
):
    if isinstance(event, Message):
        await event.answer(
            text=txt.orders_moderation(),
            reply_markup=await ikb.orders_menu()
        )
    else:
        await event.message.edit_text(
            text=txt.orders_moderation(),
            reply_markup=await ikb.orders_menu()
        )


@router.callback_query(or_f(Manager(), Director()), F.data.in_({'ModerationApplications', 'BackToModerationApplications'}))
async def moderation_applications(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    await open_moderation_applications(
        callback=callback,
        state=state
    )


@router.callback_query(or_f(Manager(), Director()), F.data == 'ForwardModerationOrder')
async def moderation_applications(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    count = await db.get_orders_count_for_applications_moderation()

    if count > 0:
        data = await state.get_data()
        await callback.message.edit_text(
            text=txt.order_applications_info(),
            reply_markup=await ikb.orders_info(
                index=data['index'] + 5,
                page=data['moder_order_page'] + 1
            )
        )
        await state.update_data(
            moder_order_page=data['moder_order_page'] + 1,
            index=data['index'] + 5
        )
    else:
        await callback.message.edit_text(
            text=txt.no_applications_moderation(),
            reply_markup=ikb.back_to_moderation_menu()
        )


@router.callback_query(or_f(Manager(), Director()), F.data == 'BackModerationOrder')
async def moderation_applications(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    count = await db.get_orders_count_for_applications_moderation()

    if count > 0:
        data = await state.get_data()

        await callback.message.edit_text(
            text=txt.order_applications_info(),
            reply_markup=await ikb.orders_info(
                index=data['index'] - 5,
                page=data['moder_order_page'] - 1
            )
        )
        await state.update_data(
            moder_order_page=data['moder_order_page'] - 1,
            index=data['index'] - 5
        )
    else:
        await callback.message.edit_text(
            text=txt.no_applications_moderation(),
            reply_markup=ikb.back_to_moderation_menu()
        )


@router.callback_query(or_f(Manager(), Director()), F.data.startswith('ManagerModerationOrder:'))
async def open_moder_order(
        callback: CallbackQuery
):
    await callback.answer()
    order_id = int(callback.data.split(':')[1])
    order = await db.get_order(order_id=order_id)
    workers_count = await db.get_order_workers_count_by_order_id(order_id=order_id)
    applications_count = await db.get_applications_count_by_order_id(order_id=order_id)

    await callback.message.edit_text(
        text=await txt.moderation_order_info(
            city=order.city,
            customer_id=order.customer_id,
            job=order.job_name,
            date=order.date,
            day_shift=order.day_shift,
            night_shift=order.night_shift,
            amount=order.amount,
            workers_count=workers_count,
            order_workers=order.workers,
            applications_count=applications_count),
        reply_markup=ikb.moder_order_info(
            order_id=order_id
        )
    )


@router.callback_query(or_f(Manager(), Director()), F.data.startswith('PreviewPdf:'))
async def preview_pdf(
        callback: CallbackQuery
):
    order_id = int(callback.data.split(':')[1])
    workers = await db.get_workers_for_pdf(order_id=order_id)

    if workers:
        await callback.answer(
            text=txt.order_pdf(),
            show_alert=True
        )

        order = await db.get_order(order_id=order_id)
        customer = await db.get_customer_info(customer_id=order.customer_id)

        director = await db.get_director_by_tg_id(callback.from_user.id)
        if director:
            position = "Директор"
            manager_name = director.full_name
        else:
            manager = await db.get_manager(callback.from_user.id)
            position = "Менеджер"
            manager_name = manager.manager_full_name if manager else None

        generator = PdfGenerator()
        shift = order.day_shift if order.day_shift else order.night_shift
        pdf_data = {
            'order_id': order.id,
            'city': order.city,
            'organization': customer.organization,
            'date': order.date,
            'start_shift': shift.split('-')[0],
            'end_shift': shift.split('-')[1],
            'manager_position': position,
            'manager_name': manager_name,
            'manager_tg_id': callback.from_user.id,
            'workers': [
                {'last_name': workers[worker_id]['last_name'],
                 'first_name': workers[worker_id]['first_name'],
                 'middle_name': workers[worker_id]['middle_name'],
                 'position': order.job_name}
                for worker_id in workers
            ]
        }

        pdf_bytes = await generator.generate_pdf_start_shift(data=pdf_data)

        shift_name = 'Д' if order.day_shift else 'Н'
        pdf_date = datetime.strptime(order.date, '%d.%m.%Y')
        pdf_name = f"{customer.organization} {datetime.strftime(pdf_date, '%d_%m_%y')}_{shift_name}.pdf"

        await callback.message.answer_document(
            document=BufferedInputFile(
                file=pdf_bytes,
                filename=pdf_name
            ),
            caption=txt.order_pdf_info()
        )
    else:
        await callback.answer(
            text=txt.workers_none_pdf(),
            show_alert=True
        )


@router.callback_query(or_f(Manager(), Director()), F.data.startswith('CompleteRegistration:'))
async def confirmation_complete_registration_order(
        callback: CallbackQuery
):
    order_id = int(callback.data.split(':')[1])
    workers = await db.get_workers_for_pdf(order_id=order_id)

    if workers:
        await callback.message.edit_text(
            text=txt.accept_complete_registration_order(),
            reply_markup=ikb.accept_complete_registration(
                order_id=order_id
            )
        )
    else:
        await callback.answer(
            text=txt.workers_none_registration(),
            show_alert=True
        )


@router.callback_query(or_f(Manager(), Director()), F.data.startswith('ConfirmCompleteRegistration:'))
async def registration_completed(
        callback: CallbackQuery,
        state: FSMContext
):
    try:
        order = await db.get_order(
            order_id=int(callback.data.split(':')[1])
        )

        await db.order_set_in_progress(
            order_id=order.id,
            manager_tg_id=callback.from_user.id
        )

        # Phase 5.1: добавить исполнителей в смену CRM РР (если заявка привязана к смене)
        if order.rr_shift_id:
            from API.shift_gateway import add_worker_to_shift
            worker_ids = await db.get_order_workers_id_by_order_id(order_id=order.id)
            for wid in worker_ids:
                worker_user = await db.get_user_by_id(user_id=wid)
                if worker_user and worker_user.api_id:
                    try:
                        await add_worker_to_shift(
                            shift_id=order.rr_shift_id,
                            worker_id=worker_user.api_id,
                        )
                    except Exception as rr_exc:
                        logging.warning(
                            f'[Phase5.1] add_worker_to_shift failed: worker={wid}, '
                            f'shift={order.rr_shift_id}: {rr_exc}'
                        )

        await schedule_call_campaign(order_id=order.id)

        await callback.answer(
            text=txt.registration_completed(),
            show_alert=True
        )

        director = await db.get_director_by_tg_id(callback.from_user.id)
        if director:
            position = "Директор"
            manager_name = director.full_name
        else:
            manager = await db.get_manager(callback.from_user.id)
            position = "Менеджер"
            manager_name = manager.manager_full_name if manager else None

        customer = await db.get_customer_info(customer_id=order.customer_id)
        customer_admins = await db.get_customer_admins(customer_id=order.customer_id)
        workers_for_pdf = await db.get_workers_for_pdf(order_id=order.id)

        generator = PdfGenerator()
        shift = order.day_shift if order.day_shift else order.night_shift
        pdf_data = {
            'order_id': order.id,
            'city': order.city,
            'organization': customer.organization,
            'date': order.date,
            'start_shift': shift.split('-')[0],
            'end_shift': shift.split('-')[1],
            'manager_position': position,
            'manager_name': manager_name,
            'manager_tg_id': callback.from_user.id,
            'workers': [
                {'last_name': workers_for_pdf[worker_id]['last_name'],
                 'first_name': workers_for_pdf[worker_id]['first_name'],
                 'middle_name': workers_for_pdf[worker_id]['middle_name'],
                 'position': order.job_name}
                for worker_id in workers_for_pdf
            ]
        }

        pdf_bytes = await generator.generate_pdf_start_shift(data=pdf_data)

        shift_name = 'Д' if order.day_shift else 'Н'
        pdf_date = datetime.strptime(order.date, '%d.%m.%Y')
        file_name = f"{customer.organization} {datetime.strftime(pdf_date, '%d_%m_%y')}_{shift_name}.pdf"

        for admin in customer_admins:
            try:
                await callback.bot.send_document(
                    chat_id=admin.admin,
                    document=BufferedInputFile(
                        file=pdf_bytes,
                        filename=file_name
                    ),
                    caption=txt.pdf_order_start_shift(
                        order_id=order.id,
                        date=order.date,
                        day_shift=order.day_shift,
                        night_shift=order.night_shift
                    )
                )
            except:
                pass

        customer_groups = await db.get_customer_groups(
            customer_id=order.customer_id
        )
        photos = convert_pdf_pages_to_byte_streams(
            pdf_data=pdf_bytes
        )
        for group in customer_groups:
            try:
                await callback.bot.send_photo(
                    chat_id=group.chat_id,
                    photo=BufferedInputFile(
                        file=photos[0],
                        filename=file_name
                    ),
                    caption=txt.send_order_photo_start_shift(
                        date=datetime.strftime(pdf_date, '%d.%m.%Y'),
                        shift=shift_name
                    )
                )
            except:
                pass

        # Отправка на email (новый функционал)
        from utils.email.email_sender import send_worker_list_email, parse_email_addresses

        email_addresses, email_sending_enabled = await db.get_customer_email_settings(order.customer_id)

        if email_sending_enabled and email_addresses:
            # Проверяем время последней отправки письма (минимум 2 минуты между отправками)
            can_send, last_sent_time = await db.check_last_email_sent_time(
                order_id=order.id,
                order_date=order.date,
                shift=shift_name,
                min_interval_minutes=2
            )

            if can_send:
                # Получаем email адреса заказчика
                customer_emails = parse_email_addresses(email_addresses)

                # Получаем внутренние email платформы
                platform_emails_str = await db.get_platform_emails()
                platform_emails = parse_email_addresses(platform_emails_str) if platform_emails_str else []

                # Объединяем все email адреса
                all_recipients = customer_emails + platform_emails

                if all_recipients:
                    # Отправляем email
                    success, error_message = await send_worker_list_email(
                        recipient_emails=all_recipients,
                        order_date=order.date,
                        shift_name=shift_name,
                        work_cycle=order.work_cycle,
                        pdf_bytes=pdf_bytes,
                        pdf_filename=file_name
                    )

                    # Логируем результат отправки
                    email_type = 'PRIMARY' if order.work_cycle == 1 else 'UPDATED'
                    await db.log_email_sending(
                        order_id=order.id,
                        order_date=order.date,
                        shift=shift_name,
                        work_cycle=order.work_cycle,
                        email_type=email_type,
                        recipients='; '.join(all_recipients),
                        status='OK' if success else 'ERROR',
                        error_message=error_message
                    )
                    if success:
                        async with async_session() as session:
                            await session.execute(
                                update(Order)
                                .where(Order.id == order.id)
                                .values(work_cycle=order.work_cycle + 1)
                            )
                            await session.commit()
            else:
                # Письмо не отправлено из-за временного ограничения (менее 2 минут с последней отправки)
                await db.log_email_sending(
                    order_id=order.id,
                    order_date=order.date,
                    shift=shift_name,
                    work_cycle=order.work_cycle,
                    email_type='SKIPPED',
                    recipients=email_addresses,
                    status='SKIPPED',
                    error_message=f'Письмо пропущено: с последней отправки прошло менее 2 минут (последняя отправка: {last_sent_time})'
                )
        elif email_sending_enabled and not email_addresses:
            # Галочка активна, но email не заполнены - логируем как ошибку
            await db.log_email_sending(
                order_id=order.id,
                order_date=order.date,
                shift=shift_name,
                work_cycle=order.work_cycle,
                email_type='PRIMARY' if order.work_cycle == 1 else 'UPDATED',
                recipients='',
                status='ERROR',
                error_message='Email адреса не указаны, но отправка включена'
            )

        applications = await db.get_applications_by_order_id(order_id=order.id)
        day = get_day_of_week_by_date(date=order.date)
        for application in applications:
            try:
                user = await db.get_user_by_id(user_id=application.worker_id)
                await callback.bot.send_message(
                    chat_id=user.tg_id,
                    text=await txt.rejected_user_application(
                        city=order.city,
                        customer_id=order.customer_id,
                        job=order.job_name,
                        date=order.date,
                        day_shift=order.day_shift,
                        night_shift=order.night_shift,
                        amount=order.amount,
                        day=day
                    ),
                    protect_content=True
                )
            except:
                pass
        order_workers_tg_id = await db.get_order_workers_tg_id(
            order_id=order.id
        )
        for tg_id in order_workers_tg_id:
            try:
                worker = await db.get_user_with_data_for_security(
                    tg_id=tg_id,
                )
                in_progress_text = txt.order_in_progress_notification(
                    order_date=order.date,
                    order_time=order.day_shift if order.day_shift else order.night_shift,
                    worker_full_name=f'{worker.security.first_name} {worker.security.middle_name} {worker.security.last_name}',
                )
                await callback.bot.send_message(
                    chat_id=tg_id,
                    text=in_progress_text,
                    protect_content=True
                )
                await db.add_web_panel_notification(
                    worker_id=worker.id,
                    title='Услуга согласована и подтверждена',
                    body=strip_html_plain(in_progress_text),
                )
            except:
                pass

        await schedule_customer_order_notifications(
            customer_id=order.customer_id,
            order_id=order.id
        )
        await db.delete_applications_by_order_id(order_id=order.id)
    except Exception as e:
        logging.exception(f'\n\n{e}')
        await callback.answer(
            text=txt.registration_complete_error(),
            show_alert=True
        )
    finally:
        await open_moderation_applications(
            callback=callback,
            state=state
        )


@router.callback_query(or_f(Manager(), Director()), F.data.startswith('ChangeWorkersCount:'))
async def change_workers_count_start(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    order_id = int(callback.data.split(':')[1])
    await state.update_data(change_workers_order_id=order_id)
    await state.set_state('ChangeWorkersCount')
    await callback.message.edit_text(
        text='👥 Введите новое количество исполнителей:'
    )


@router.message(or_f(Manager(), Director()), F.text, StateFilter('ChangeWorkersCount'))
async def change_workers_count_save(
        message: Message,
        state: FSMContext
):
    try:
        workers = int(message.text.strip())
    except ValueError:
        await message.answer(text='❗ Введите целое число')
        return

    data = await state.get_data()
    order_id = data.get('change_workers_order_id')
    await state.clear()

    await db.set_order_workers_count(order_id=order_id, workers=workers)

    order = await db.get_order(order_id=order_id)
    organization = await db.get_customer_organization(customer_id=order.customer_id)

    await message.answer(
        text=txt.order_moderation(
            organization=organization,
            job=order.job_name,
            date=order.date,
            day_shift=order.day_shift,
            night_shift=order.night_shift,
            workers=order.workers
        ),
        reply_markup=await ikb.order_moder(page=1, order_id=order_id)
    )
