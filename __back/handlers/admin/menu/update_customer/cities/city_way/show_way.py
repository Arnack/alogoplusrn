from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto
from typing import NoReturn

import keyboards.inline as ikb
from filters import Admin, admin_filter
import database as db
import texts as txt


router = Router()


@router.callback_query(Admin(), F.data.startswith('UpdateCustomerCityWay:'))
async def show_city_way(
        callback: CallbackQuery
):
    await callback.answer()
    city_id = int(callback.data.split(':')[1])
    city_way = await db.get_customer_city_way(
        city_id=city_id
    )
    if city_way:
        await callback.message.edit_text(
            text=txt.customer_city_way(),
            reply_markup=ikb.update_city_way(
                city_id=city_id
            )
        )
    else:
        await callback.message.edit_text(
            text=txt.no_customer_city_way(),
            reply_markup=ikb.add_city_way(
                city_id=city_id
            )
        )


async def show_customer_city_way(
        callback: CallbackQuery
) -> NoReturn:
    await callback.answer()
    city_id = int(callback.data.split(':')[1])
    city_way = await db.get_customer_city_way(
        city_id=city_id
    )

    is_admin = admin_filter(
        worker_id=callback.from_user.id
    )
    if city_way:
        protect = not is_admin
        photos = [item.photo for item in city_way.city_photos]
        if photos:
            if len(photos) == 1:
                await callback.message.answer_photo(
                    photo=photos[0],
                    caption=txt.admin_city_way_caption(
                        description=city_way.way_to_job
                    ),
                    protect_content=protect
                )
            else:
                await callback.message.answer_media_group(
                    media=[
                        InputMediaPhoto(
                            media=photos[0],
                            caption=txt.admin_city_way_caption(
                                description=city_way.way_to_job
                            ),
                        ),
                        InputMediaPhoto(
                            media=photos[1]
                        )
                    ],
                    protect_content=protect
                )
        else:
            await callback.message.answer(
                text=txt.admin_city_way_caption(
                    description=city_way.way_to_job
                ),
                protect_content=protect
            )
    else:
        if is_admin:
            await callback.message.edit_text(
                text=txt.no_customer_city_way(),
                reply_markup=ikb.add_city_way(
                    city_id=city_id
                )
            )


@router.callback_query(Admin(), F.data.startswith('ShowCityWay:'))
async def show_city_way(
        callback: CallbackQuery
):
    await show_customer_city_way(
        callback=callback
    )
