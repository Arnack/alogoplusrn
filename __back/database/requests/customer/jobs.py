from database import CustomerJob, CustomerAdmin, async_session
from sqlalchemy import select


async def get_customer_admin_jobs(admin):
    async with async_session() as session:
        customer_id = await session.scalar(select(CustomerAdmin.customer_id).where(CustomerAdmin.admin == admin))
        return await session.scalars(select(CustomerJob.job).where(CustomerJob.customer_id == customer_id))
