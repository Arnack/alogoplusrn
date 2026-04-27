from aiogram.fsm.context import FSMContext
from typing import List


async def delete_state_data(
        state: FSMContext,
        data_keys_to_delete: List[str]
) -> None:
    """
        Функция для удаления конкретных данных из хранилища состояний по ключу
        :param state:
        :param data_keys_to_delete: Список с ключами
        :return: None
    """
    data = await state.get_data()

    for key in data_keys_to_delete:
        try:
            del data[key]
        except KeyError:
            pass

    await state.set_data(data)
