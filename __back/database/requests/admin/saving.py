from database import Saving, Customer, async_session
from sqlalchemy import select, func
from decimal import Decimal


async def set_or_update_saving(
        customer_id: int,
        saving_amount: str,
        total_amount: str,
        date: str
) -> None:
    async with async_session() as session:
        saving = await session.scalar(
            select(Saving).where(
                Saving.customer_id == customer_id,
                Saving.date == date
            )
        )
        if not saving:
            session.add(
                Saving(
                    customer_id=customer_id,
                    saving_amount=saving_amount,
                    total_amount=total_amount,
                    date=date
                )
            )
        else:
            saving.saving_amount = str(Decimal(saving.saving_amount) + Decimal(saving_amount))
            saving.total_amount = str(Decimal(saving.total_amount) + Decimal(total_amount))
        await session.commit()


async def get_saving(
        start_date_str: str,
        end_date_str: str
) -> dict:
    async with async_session() as session:
        start_date = func.to_date(start_date_str, 'DD.MM.YYYY')
        end_date = func.to_date(end_date_str, 'DD.MM.YYYY')

        customers = await session.scalars(
            select(Customer)
        )
        result = {}
        for customer in customers:
            savings = await session.scalars(
                select(Saving).where(
                    Saving.customer_id == customer.id,
                    func.to_date(
                        Saving.date, 'DD.MM.YYYY'
                    ).between(
                        start_date, end_date
                    )
                )
            )

            savings = savings.all()
            if not savings:
                result[customer.organization] = {
                    'total_sum': '0',
                    'saving_sum': '0',
                    'saving': '0',
                }
            else:
                total_sum = sum(map(Decimal, [saving.total_amount for saving in savings]))
                saving_sum = sum(map(Decimal, [saving.saving_amount for saving in savings]))
                saving = total_sum - saving_sum
                result[customer.organization] = {
                    'total_sum': str(total_sum),
                    'saving_sum': str(saving_sum),
                    'saving': str(saving),
                }
        return result
