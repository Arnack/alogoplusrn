from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile
from datetime import datetime

from filters import Accountant
import database as db
from utils import PdfGenerator


router = Router()


@router.message(Accountant(), F.text == '📊 Баланс начислений')
async def send_balance_report(message: Message):
    await message.answer('⏳ Формирую PDF отчёт...')

    workers = await db.get_workers_with_nonzero_balance()

    if not workers:
        await message.answer('ℹ️ Нет работников с ненулевым балансом начислений.')
        return

    generator = PdfGenerator()
    pdf_bytes = await generator.generate_pdf_balance_report(workers=workers)

    date_str = datetime.now().strftime('%d_%m_%Y')
    await message.answer_document(
        document=BufferedInputFile(
            file=pdf_bytes,
            filename=f'Баланс_начислений_{date_str}.pdf',
        ),
        caption=f'📊 Баланс начислений — {len(workers)} исполнителей',
    )
