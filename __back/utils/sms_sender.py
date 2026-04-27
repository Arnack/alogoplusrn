from config_reader import config
import aiohttp

from utils.loggers.api import write_api_log


async def send_sms_with_api(
        phone_number: str,
        message_text: str,
        tg_id: int,
) -> None:
    url = f"https://api.iqsms.ru/messages/v2/send/?phone={phone_number}&text={message_text}"
    auth = aiohttp.BasicAuth(
        login=config.sms_api_login.get_secret_value(),
        password=config.sms_api_password.get_secret_value()
    )

    async with aiohttp.ClientSession(auth=auth) as session:
        async with session.get(url) as response:
            write_api_log(
                status_code=response.status,
                data=f"Пользователь {tg_id}. Статус отправки смс: {response.status} | {await response.text()}",
            )
            if response.status != 200:
                write_api_log(
                    status_code=response.status,
                    data=f'Ошибка при отправке SMS: {response.status} | {await response.text()}',
                    level='ERROR',
                )
