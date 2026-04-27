from database import OrderApplication, async_session
from sqlalchemy import delete


async def delete_application(application_id):
    async with async_session() as session:
        await session.execute(delete(OrderApplication).where(OrderApplication.id == application_id))
        await session.commit()
