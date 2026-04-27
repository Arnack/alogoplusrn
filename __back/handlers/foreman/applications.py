from aiogram import Router, F
from aiogram.types import CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from datetime import datetime

from utils.pdf.pdf_generator import PdfGenerator
import keyboards.inline as ikb
import database as db
import texts as txt


router = Router()


@router.callback_query(F.data.startswith('ForemanShowOrderApplications:'))
async def foreman_show_order_application(
        callback: CallbackQuery
):
    order_id = int(callback.data.split(':')[1])
    applications = await db.get_applications_for_moderation(order_id=order_id)

    if applications:
        await callback.answer()
        await callback.message.edit_text(
            text=txt.foreman_applications_menu(),
            reply_markup=await ikb.foreman_applications_menu(
                applications=applications
            )
        )
    else:
        await callback.answer(
            text=txt.foreman_no_order_applications(),
            show_alert=True
        )


@router.callback_query(F.data.startswith('ForemanGetPdfWithWorkers:'))
async def show_pdf_with_order_workers(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer(
        text=txt.foreman_pdf_info(),
        show_alert=True
    )

    generator = PdfGenerator()
    order_id = int(callback.data.split(':')[1])
    order = await db.get_order(
        order_id=order_id
    )
    customer = await db.get_customer_info(
        customer_id=order.customer_id
    )
    order_workers = await db.get_order_workers_id_by_order_id(
        order_id=order_id
    )
    workers = []
    data = await state.get_data()
    for w_id in order_workers:
        if w_id == data['ForemanWorkerID']:
            continue
        workers.append(
            await db.get_user_real_data_by_id(
                user_id=w_id
            )
        )

    pdf_data = {
        'city': order.city,
        'organization': customer.organization,
        'date': order.date,
        'day_shift': order.day_shift,
        'night_shift': order.night_shift,
        'workers': [
            {'FullName': f'{worker.last_name} {worker.first_name} {worker.middle_name if worker.middle_name else ""}'}
            for worker in workers
        ]
    }

    pdf_bytes = await generator.generate_pdf_for_foreman(data=pdf_data)

    shift_name = 'Д' if order.day_shift else 'Н'
    pdf_date = datetime.strptime(order.date, '%d.%m.%Y')
    pdf_name = f"{customer.organization} {datetime.strftime(pdf_date, '%d_%m_%y')}_{shift_name}.pdf"

    await callback.message.answer_document(
        document=BufferedInputFile(
            file=pdf_bytes,
            filename=pdf_name
        ),
        caption=txt.order_pdf_info(),
        protect_content=True
    )
