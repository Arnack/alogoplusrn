from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter, or_f

from filters import Manager, Director
import keyboards.inline as ikb
import database as db
from utils.pdf import generate_workers_pdf
import logging


router = Router()


# Обработчик reply-кнопки "🔍 СМЗ"
@router.message(or_f(Manager(), Director()), F.text == '🔍 СМЗ')
async def workers_view_start(message: Message, state: FSMContext):
    """Начало просмотра самозанятых - показываем выбор города"""
    await state.clear()

    # Сразу показываем выбор города (БЕЗ текста сверху)
    await message.answer(
        text='Выберите город:',
        reply_markup=await ikb.cities_for_workers()
    )


# Обработчик выбора города
@router.callback_query(or_f(Manager(), Director()), F.data.startswith('WorkersViewCity:'))
async def workers_view_city_selected(callback: CallbackQuery, state: FSMContext):
    """После выбора города показываем 3 кнопки"""
    city = callback.data.split(':')[1]

    # Сохраняем выбранный город в состояние
    await state.update_data(selected_city=city)

    # Показываем меню (БЕЗ текста сверху)
    await callback.message.edit_text(
        text=f'Город: {city}',
        reply_markup=ikb.workers_menu()
    )


# ========== 📄 Сформировать PDF ==========

@router.callback_query(or_f(Manager(), Director()), F.data == 'WorkersViewPDF')
async def workers_view_generate_pdf(callback: CallbackQuery, state: FSMContext):
    """Формирование и отправка PDF со списком самозанятых"""
    data = await state.get_data()
    city = data.get('selected_city')

    if not city:
        await callback.answer('Ошибка: город не выбран')
        return

    # Получаем самозанятых из города
    workers = await db.get_workers_by_city(city)

    if not workers:
        await callback.answer('В этом городе нет исполнителей (НПД)')
        return

    try:
        # Загружаем последние WEB IP для всех исполнителей
        worker_ids = [w.id for w in workers]
        workers_ip = await db.get_workers_last_web_ip(worker_ids)

        # Генерируем PDF
        pdf_buffer = await generate_workers_pdf(workers, city, workers_ip=workers_ip)

        # Отправляем PDF менеджеру
        pdf_file = BufferedInputFile(
            pdf_buffer.read(),
            filename=f'исполнители_{city}.pdf'
        )

        await callback.message.answer_document(pdf_file)
        await callback.answer()

    except Exception as e:
        logging.exception(f'Error generating workers PDF: {e}')
        await callback.answer('Ошибка при формировании PDF')


# ========== 🔍 Поиск по ФИО ==========

@router.callback_query(or_f(Manager(), Director()), F.data == 'WorkersViewSearch')
async def workers_view_search_start(callback: CallbackQuery, state: FSMContext):
    """Начало поиска по фамилии"""
    await state.set_state('WorkersViewSearchLastName')

    # Сразу запрашиваем фамилию (БЕЗ инструкций)
    await callback.message.edit_text(text='Введите фамилию:')


@router.message(or_f(Manager(), Director()), StateFilter('WorkersViewSearchLastName'))
async def workers_view_search_process(message: Message, state: FSMContext):
    """Обработка введённой фамилии и показ результатов"""
    last_name = message.text.strip()
    data = await state.get_data()
    city = data.get('selected_city')

    if not city:
        await message.answer('Ошибка: город не выбран')
        await state.set_state(None)
        return

    # Ищем самозанятых по фамилии
    workers = await db.search_workers_by_last_name(city, last_name)

    if not workers:
        # Человек НЕ найден
        await message.answer('Такого исполнителя (НПД) в данном городе нет')
        await state.set_state(None)
        return

    if len(workers) == 1:
        # Найден один человек - сразу показываем ФИО и телефон
        worker = workers[0]
        await show_worker_info(message, worker, last_name)
        await state.set_state(None)
    else:
        # Найдено несколько - показываем список
        await message.answer(
            text='Выберите исполнителя (НПД):',
            reply_markup=ikb.search_results_keyboard(workers, last_name)
        )
        await state.set_state(None)


@router.callback_query(or_f(Manager(), Director()), F.data.startswith('WorkersViewSearchResult:'))
async def workers_view_search_result_selected(callback: CallbackQuery):
    """Показ выбранного человека из результатов поиска"""
    parts = callback.data.split(':')
    worker_id = int(parts[1])
    search_query = parts[2]

    worker = await db.get_worker_by_id(worker_id)

    if worker:
        await show_worker_info(callback.message, worker, search_query)
    else:
        await callback.answer('Исполнитель (НПД) не найден')


# ========== 🔍 Поиск по всем участкам ==========

@router.callback_query(or_f(Manager(), Director()), F.data == 'WorkersViewSearchAll')
async def workers_view_search_all_start(callback: CallbackQuery, state: FSMContext):
    """Начало поиска по всем участкам"""
    await state.set_state('WorkersViewSearchAllLastName')

    # Запрашиваем фамилию
    await callback.message.edit_text(text='Введите фамилию для поиска по всем участкам:')


@router.message(or_f(Manager(), Director()), StateFilter('WorkersViewSearchAllLastName'))
async def workers_view_search_all_process(message: Message, state: FSMContext):
    """Обработка введённой фамилии и показ результатов по всем участкам"""
    last_name = message.text.strip()

    # Ищем самозанятых по фамилии во всех городах
    workers = await db.search_workers_all_cities(last_name)

    if not workers:
        # Человек НЕ найден
        await message.answer('Такого исполнителя (НПД) не найдено')
        await state.clear()
        return

    if len(workers) == 1:
        # Найден один человек - сразу показываем ФИО и телефон
        worker = workers[0]
        await show_worker_info(message, worker, last_name)
        await state.clear()
    else:
        # Найдено несколько - показываем список с указанием города
        await message.answer(
            text='Выберите исполнителя (НПД):',
            reply_markup=ikb.search_results_keyboard_with_city(workers, last_name)
        )
        await state.clear()


@router.callback_query(or_f(Manager(), Director()), F.data.startswith('WorkersViewSearchAllResult:'))
async def workers_view_search_all_result_selected(callback: CallbackQuery):
    """Показ выбранного человека из результатов поиска по всем участкам"""
    parts = callback.data.split(':')
    worker_id = int(parts[1])
    search_query = parts[2]

    worker = await db.get_worker_by_id(worker_id)

    if worker:
        await show_worker_info(callback.message, worker, search_query)
    else:
        await callback.answer('Исполнитель (НПД) не найден')


# ========== 📋 Люди ==========

@router.callback_query(or_f(Manager(), Director()), F.data == 'WorkersViewPeople')
async def workers_view_people_start(callback: CallbackQuery, state: FSMContext):
    """Показ списка людей (первая страница)"""
    await show_workers_page(callback.message, state, page=0)


@router.callback_query(or_f(Manager(), Director()), F.data.startswith('WorkersViewPeoplePage:'))
async def workers_view_people_page(callback: CallbackQuery, state: FSMContext):
    """Навигация по страницам списка людей"""
    page = int(callback.data.split(':')[1])
    await show_workers_page(callback.message, state, page, edit=True)


@router.callback_query(or_f(Manager(), Director()), F.data.startswith('WorkersViewPerson:'))
async def workers_view_person_selected(callback: CallbackQuery):
    """Показ информации о выбранном человеке"""
    worker_id = int(callback.data.split(':')[1])
    worker = await db.get_worker_by_id(worker_id)

    if worker:
        await show_worker_info(callback.message, worker)
    else:
        await callback.answer('Исполнитель (НПД) не найден')


# ========== Вспомогательные функции ==========

async def show_workers_page(message: Message, state: FSMContext, page: int = 0, edit: bool = False):
    """
    Показывает страницу со списком самозанятых

    Args:
        message: Объект сообщения
        state: FSM контекст
        page: Номер страницы (начиная с 0)
        edit: Редактировать существующее сообщение или отправить новое
    """
    data = await state.get_data()
    city = data.get('selected_city')

    if not city:
        await message.answer('Ошибка: город не выбран')
        return

    # Получаем всех самозанятых из города
    all_workers = await db.get_workers_by_city(city)

    if not all_workers:
        text = 'В этом городе нет исполнителей (НПД)'
        if edit:
            await message.edit_text(text)
        else:
            await message.answer(text)
        return

    # Пагинация: 20 человек на страницу
    workers_per_page = 20
    total_pages = (len(all_workers) + workers_per_page - 1) // workers_per_page

    # Валидация номера страницы
    if page < 0:
        page = 0
    elif page >= total_pages:
        page = total_pages - 1

    # Получаем самозанятых для текущей страницы
    start_idx = page * workers_per_page
    end_idx = start_idx + workers_per_page
    workers_on_page = all_workers[start_idx:end_idx]

    # Формируем клавиатуру
    keyboard = ikb.workers_list_keyboard(workers_on_page, page, total_pages)
    text = f"Страница {page + 1} из {total_pages}"
    # Показываем список (БЕЗ текста сверху)
    if edit:
        await message.edit_text(
            text=text,
            reply_markup=keyboard
        )
    else:
        await message.answer(
            text=text,
            reply_markup=keyboard
        )


async def show_worker_info(message: Message, worker: db.User, search_query: str = None):
    """
    Показывает информацию о самозанятом: ФИО, введенный телефон и реальный телефон

    Args:
        message: Объект сообщения
        worker: Объект самозанятого
        search_query: Фамилия из поиска (чтобы она оставалась видна)
    """
    # Формируем полное ФИО (ФАМИЛИЯ заглавными)
    full_name = f'{worker.last_name.upper()} {worker.first_name}'
    if worker.middle_name:
        full_name += f' {worker.middle_name}'

    # Получаем реальные данные из РР
    real_data = await db.get_user_real_data_by_id(user_id=worker.id)

    # Форматируем введенный телефон (кликабельный)
    if worker.phone_number and len(worker.phone_number) == 12 and worker.phone_number.startswith('+7'):
        phone_link = f'<a href="tel:{worker.phone_number}">{worker.phone_number}</a>'
    else:
        phone_link = 'Не указан'

    # Форматируем реальный телефон (кликабельный)
    if real_data and real_data.phone_number:
        real_phone = real_data.phone_number
        if len(real_phone) == 12 and real_phone.startswith('+7'):
            real_phone_link = f'<a href="tel:{real_phone}">{real_phone}</a>'
        else:
            real_phone_link = real_phone
    else:
        real_phone_link = 'Не указан'

    # Формируем текст сообщения
    text = (
        f'{full_name}\n'
        f'📱 Номер телефона: {phone_link}\n'
        f'📱 Реальный номер: {real_phone_link}'
    )

    await message.answer(text, parse_mode='HTML')
