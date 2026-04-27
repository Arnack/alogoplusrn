from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
import secrets

from handlers.user.menu.search_orders import open_customer_search_menu
from utils import (
    normalize_phone_number, create_code_hash,
    schedule_delete_code_for_order, send_sms_with_api,
    check_code, friend_logger
)
import keyboards.inline as ikb
from filters import Worker
import database as db
import texts as txt
import API


router = Router()
router.message.filter(Worker())
router.callback_query.filter(Worker())


@router.message(F.text == '💼 Заявка для друга')
async def order_for_friend(
        message: Message
):
    await message.answer(
        text=txt.order_for_friend_confirmation(),
        reply_markup=ikb.order_for_friend_confirmation(),
        protect_content=True
    )
    friend_logger.info(
        f"Пользователь {message.from_user.id} воспользовался разделом \"💼 Заявка для друга\""
    )


@router.callback_query(F.data == 'CancelOrderForFriend')
async def cancel_order_for_friend(
        callback: CallbackQuery
):
    await callback.answer()
    await callback.message.delete()
    friend_logger.info(
        f"Пользователь {callback.from_user.id} вышел из раздела \"💼 Заявка для друга\""
    )


@router.callback_query(F.data == 'ContinueOrderForFriend')
async def continue_order_for_friend(
        callback: CallbackQuery
):
    await callback.answer()
    await callback.message.edit_text(
        text=txt.choose_method_search_friend(),
        reply_markup=ikb.methods_search_friend(),
        protect_content=True
    )
    friend_logger.info(
        f"Пользователь {callback.from_user.id} продолжил работу с разделом \"💼 Заявка для друга\""
    )


@router.callback_query(F.data == 'SearchWorkerByPhone')
async def continue_order_for_friend(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    await callback.message.edit_text(
        text=txt.request_worker_phone_number(),
        protect_content=True
    )
    await state.set_state(
        'SearchWorkerByPhone'
    )
    friend_logger.info(
        f"Пользователь {callback.from_user.id} выбрал поиск по номеру телефона"
    )


@router.message(F.text, StateFilter('SearchWorkerByPhone'))
async def get_worker_phone(
        message: Message,
        state: FSMContext
):
    phone_number = normalize_phone_number(message.text)
    if phone_number:
        friend_logger.info(
            f"Пользователь {message.from_user.id}. Номера телефона корректен"
        )
        await state.set_state(None)
        msg = await message.answer(
            text=txt.worker_search(),
            protect_content=True
        )
        friend = await db.get_worker_by_phone_number(
            phone_number=phone_number
        )
        if friend:
            real_data = await db.get_user_real_data_by_id(
                user_id=friend.id
            )
            friend_logger.info(
                f"Пользователь {message.from_user.id}. "
                f"Друг [{real_data.last_name} {real_data.first_name} {real_data.middle_name} | {real_data.phone_number}] "
                f"найден в базе данных"
            )
            await state.update_data(
                FriendID=friend.id,
                FriendCity=friend.city
            )
            if await db.check_daily_code_attempts(phone_number=real_data.phone_number):
                friend_logger.info(
                    f"Пользователь {message.from_user.id}. Запрос города для зарегистрированного пользователя"
                )
                await message.bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=msg.message_id,
                    text=txt.choose_friend_city(),
                    reply_markup=await ikb.cities_for_order_for_friend()
                )
                await state.update_data(
                    ChooseCityAction='RegWorker',
                    FriendID=friend.id,
                    PhoneNumber=real_data.phone_number,
                    FirstName=real_data.first_name,
                    MiddleName=real_data.middle_name,
                    LastName=real_data.last_name,
                )
            else:
                friend_logger.info(
                    f"Пользователь {message.from_user.id}. Количество попыток отправки смс превышено на сегодня"
                )
                await message.bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=msg.message_id,
                    text=txt.too_many_attempts_for_code()
                )
        else:
            friend_logger.info(
                f"Пользователь {message.from_user.id}. "
                f"Друг не зарегистрирован в боте"
            )
            worker = await API.get_worker_by_phone_number_or_inn(
                value=phone_number.lstrip('+').lstrip('7'),
            )
            if worker:
                worker_phone = worker.get('phone', '')
                friend_logger.info(
                    f"Пользователь {message.from_user.id}. "
                    f"Друг [{worker.get('lastName', '')} {worker.get('firstName', '')} {worker.get('patronymic', '')} | +7{worker_phone}] "
                    f"найден в api Рабочие руки"
                )
                await state.update_data(
                    PhoneNumber=f"+7{worker_phone}",
                    FirstName=worker.get('firstName', ''),
                    MiddleName=worker.get('patronymic', ''),
                    LastName=worker.get('lastName', ''),
                    INN=worker.get('inn', ''),
                    ApiWorkerID=worker['id'],
                    WorkerCard=worker.get('bankcardNumber', ''),
                )
                await message.bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=msg.message_id,
                    text=txt.choose_friend_city(),
                    reply_markup=await ikb.cities_for_order_for_friend()
                )
                await state.update_data(
                    ChooseCityAction='NewWorker',
                )
            else:
                await message.bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=msg.message_id,
                    text=txt.order_for_friend_worker_not_found()
                )
                friend_logger.info(
                    f"Пользователь {message.from_user.id}. Друг не найден в api Рабочие руки"
                )
    else:
        friend_logger.info(
            f"Пользователь {message.from_user.id}. "
            f"Номер телефона введен некорректно"
        )
        await message.answer(
            text=txt.phone_number_error(),
            protect_content=True
        )


@router.callback_query(F.data == 'SearchWorkerByInn')
async def continue_order_for_friend(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    await callback.message.edit_text(
        text=txt.request_worker_inn()
    )
    await state.set_state(
        'SearchWorkerByInn'
    )
    friend_logger.info(
        f"Пользователь {callback.from_user.id} выбрал поиск по ИНН"
    )


@router.message(F.text, StateFilter('SearchWorkerByInn'))
async def get_worker_phone(
        message: Message,
        state: FSMContext
):
    if message.text.isdigit():
        friend_logger.info(
            f"Пользователь {message.from_user.id}. ИНН корректен"
        )
        await state.set_state(None)
        msg = await message.answer(
            text=txt.worker_search(),
            protect_content=True
        )
        friend = await db.get_worker_by_inn(
            inn=message.text
        )
        if friend:
            real_data = await db.get_user_real_data_by_id(
                user_id=friend.id
            )
            friend_logger.info(
                f"Пользователь {message.from_user.id}. "
                f"Друг [{real_data.last_name} {real_data.first_name} {real_data.middle_name} | {real_data.phone_number}] "
                f"найден в базе данных"
            )
            await state.update_data(
                FriendID=friend.id,
                FriendCity=friend.city
            )
            if await db.check_daily_code_attempts(phone_number=real_data.phone_number):
                friend_logger.info(
                    f"Пользователь {message.from_user.id}. Запрос города для зарегистрированного пользователя"
                )
                await message.bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=msg.message_id,
                    text=txt.choose_friend_city(),
                    reply_markup=await ikb.cities_for_order_for_friend()
                )
                await state.update_data(
                    ChooseCityAction='RegWorker',
                    FriendID=friend.id,
                    PhoneNumber=real_data.phone_number,
                    FirstName=real_data.first_name,
                    MiddleName=real_data.middle_name,
                    LastName=real_data.last_name,
                )
            else:
                friend_logger.info(
                    f"Пользователь {message.from_user.id}. Количество попыток отправки смс превышено на сегодня"
                )
                await message.bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=msg.message_id,
                    text=txt.too_many_attempts_for_code()
                )
        else:
            friend_logger.info(
                f"Пользователь {message.from_user.id}. "
                f"Друг не зарегистрирован в боте"
            )
            worker = await API.get_worker_by_phone_number_or_inn(
                value=message.text,
            )
            if worker:
                worker_phone = worker.get('phone', '')
                friend_logger.info(
                    f"Пользователь {message.from_user.id}. "
                    f"Друг [{worker.get('lastName', '')} {worker.get('firstName', '')} {worker.get('patronymic', '')} | +7{worker_phone}] "
                    f"найден в api Рабочие руки"
                )
                await state.update_data(
                    PhoneNumber=f"+7{worker_phone}",
                    FirstName=worker.get('firstName', ''),
                    MiddleName=worker.get('patronymic', ''),
                    LastName=worker.get('lastName', ''),
                    INN=worker.get('inn', ''),
                    ApiWorkerID=worker['id'],
                    WorkerCard=worker.get('bankcardNumber', ''),
                )
                await message.bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=msg.message_id,
                    text=txt.choose_friend_city(),
                    reply_markup=await ikb.cities_for_order_for_friend()
                )
                await state.update_data(
                    ChooseCityAction='NewWorker',
                )
            else:
                await message.bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=msg.message_id,
                    text=txt.order_for_friend_worker_not_found()
                )
                friend_logger.info(
                    f"Пользователь {message.from_user.id}. Друг не найден в api Рабочие руки"
                )
    else:
        friend_logger.info(
            f"Пользователь {message.from_user.id}. "
            f"ИНН введен некорректно"
        )
        await message.answer(
            text=txt.add_id_error(),
            protect_content=True
        )


async def send_sms_to_worker(
        event: CallbackQuery | Message,
        state: FSMContext,
        phone_number: str,
        first_name: str,
        middle_name: str,
        last_name: str,
        message_id=None,
):
    if isinstance(event, Message):
        await event.bot.edit_message_text(
            chat_id=event.chat.id,
            message_id=message_id,
            text=txt.request_code_for_order(
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name
            )
        )
    else:
        await event.message.edit_text(
            text=txt.request_code_for_order(
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name
            )
        )
    friend_logger.info(
        f"Пользователь {event.from_user.id}. Бот просит ввести смс"
    )
    code = str(secrets.randbelow(900000) + 100000)
    code_hashed = create_code_hash(code=code)
    code_id = await db.set_code_for_order(
        code_hash=code_hashed['hash'],
        salt=code_hashed['salt']
    )
    await schedule_delete_code_for_order(
        code_id=code_id
    )
    await send_sms_with_api(
        phone_number=phone_number,
        message_text=txt.code_text_for_message(
            code=code
        ),
        tg_id=event.from_user.id
    )
    await state.set_state('CodeForOrder')
    await state.update_data(
        CodeForOrderID=code_id,
        CodeForOrderAttempts=1
    )
    del code


@router.callback_query(F.data.startswith('CityForFriend:'))
async def get_friend_city(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    data = await state.get_data()

    if data['ChooseCityAction'] == 'NewWorker':
        friend_id = await db.set_user(
            tg_id=0,
            username=None,
            phone_number=data['PhoneNumber'],
            city=callback.data.split(':')[1],
            first_name=data['FirstName'],
            middle_name=data['MiddleName'],
            last_name=data['LastName'],
            inn=data['INN'],
            real_phone_number=data['PhoneNumber'],
            real_first_name=data['FirstName'],
            real_middle_name=data['MiddleName'],
            real_last_name=data['LastName'],
            api_worker_id=data['ApiWorkerID'],
            card=data['WorkerCard'],
        )
        await state.update_data(
            FriendID=friend_id,
            FriendCity=callback.data.split(':')[1]
        )
        await db.check_daily_code_attempts(
            phone_number=data['PhoneNumber']
        )
        await send_sms_to_worker(
            event=callback,
            state=state,
            phone_number=data['PhoneNumber'],
            first_name=data['FirstName'],
            middle_name=data['MiddleName'],
            last_name=data['LastName']
        )
        friend_logger.info(
            f"Пользователь {callback.from_user.id}. Выбран город, создан виртуальный пользователь (ID: {friend_id})"
        )
    else:
        await state.update_data(
            FriendCity=callback.data.split(':')[1]
        )
        await send_sms_to_worker(
            event=callback,
            state=state,
            phone_number=data['PhoneNumber'],
            first_name=data['FirstName'],
            middle_name=data['MiddleName'],
            last_name=data['LastName']
        )
        friend_logger.info(
            f"Пользователь {callback.from_user.id}. Выбран город для зарегистрированного пользователя"
        )


@router.message(F.text, StateFilter('CodeForOrder'))
async def code_for_order_check(
        message: Message,
        state: FSMContext
):
    if message.text.isdigit():
        friend_logger.info(
            f"Получен корректный код от пользователя {message.from_user.id}"
        )
        data = await state.get_data()
        code_data = await db.get_code_for_order(
            code_id=data['CodeForOrderID']
        )
        if code_data:
            friend_logger.info(
                f"Пользователь {message.from_user.id}. Код еще активен"
            )
            checking_code = check_code(
                salt=code_data.salt,
                hashed_code=code_data.code_hash,
                entered_code=message.text
            )
            if checking_code:
                friend_logger.info(
                    f"Пользователь {message.from_user.id}. Код верный"
                )
                await db.delete_code_for_order(
                    code_id=code_data.id
                )
                friend_id = data['FriendID']
                friend_city = data['FriendCity']
                await state.clear()
                await state.update_data(
                    FriendID=friend_id,
                    FriendCity=friend_city,
                    SearchOrderFor='friend'
                )
                await open_customer_search_menu(
                    event=message,
                    state=state
                )
                friend_logger.info(
                    f"Пользователь {message.from_user.id}. Бот открыл меню выбора заявок"
                )
            else:
                if data['CodeForOrderAttempts'] >= 3:
                    friend_logger.info(
                        f"Пользователь {message.from_user.id}. Код введен неверно слишком много раз. "
                        "Бот просит попробовать позже"
                    )
                    await db.delete_code_for_order(
                        code_id=code_data.id
                    )
                    await message.answer(
                        text=txt.code_for_order_attempts_error(),
                        protect_content=True
                    )
                    await state.clear()
                else:
                    friend_logger.info(
                        f"Пользователь {message.from_user.id}. Код неверный, бот просит ввести еще раз"
                    )
                    await message.answer(
                        text=txt.code_for_order_error(),
                        protect_content=True
                    )
                    await state.update_data(
                        CodeForOrderAttempts=data['CodeForOrderAttempts'] + 1
                    )
        else:
            friend_logger.info(
                f"Пользователь {message.from_user.id}. Код уже не активен"
            )
            await message.answer(
                text=txt.the_code_has_expired_error(),
                protect_content=True
            )
            await state.clear()
    else:
        friend_logger.info(
            f"Получен некорректный код от пользователя {message.from_user.id}"
        )
        await message.answer(
            text=txt.add_id_error(),
            protect_content=True
        )
