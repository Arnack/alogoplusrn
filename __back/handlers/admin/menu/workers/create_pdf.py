from aiogram import Router, F
from aiogram.types import CallbackQuery, BufferedInputFile
from datetime import datetime

from filters import Admin, Director, Accountant
from aiogram.filters import or_f
import texts as txt
import database as db
from utils import PdfGenerator


router = Router()


@router.callback_query(or_f(Admin(), Director(), Accountant()), F.data == 'GetAllWorkersPDF')
async def create_pdf_with_workers(
        callback: CallbackQuery
):
    await callback.answer(
        text=txt.workers_pdf(),
        show_alert=True
    )

    workers = await db.get_all_workers_for_adm_pdf()
    generator = PdfGenerator()
    pdf_bytes = await generator.generate_pdf_all_workers(
        data={
            'workers': workers
        }
    )
    current_date = datetime.now()

    await callback.message.answer_document(
        document=BufferedInputFile(
            file=pdf_bytes,
            filename=f"СМЗ {datetime.strftime(current_date, '%d_%m_%y')}.pdf"
        )
    )
