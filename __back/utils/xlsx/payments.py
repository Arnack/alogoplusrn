from io import BytesIO
import pandas

from Schemas import WorkerPaymentSchema


def create_payment_xlsx(
        workers: list[WorkerPaymentSchema]
) -> bytes:
    data = [
        [
            worker.first_name,
            worker.middle_name,
            worker.last_name,
            worker.inn,
            worker.amount,
            worker.type_of_work,
            worker.card_number,
            worker.phone,
        ] for worker in workers
    ]

    df = pandas.DataFrame(
        data, columns=[
            'FIRST NAME',
            'MIDDLE NAME',
            'LAST NAME',
            'INN',
            'AMOUNT',
            'TYPE_OF_WORK',
            'CARD NUMBER',
            'PHONE',
        ]
    )

    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)
    return buffer.getvalue()
