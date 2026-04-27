from io import BytesIO
import pandas

from database import JobForPayment


def create_jobs_fp_xlsx(
        jobs_fp: list[JobForPayment]
) -> bytes:
    data = [
        [
            job.name
        ] for job in jobs_fp
    ]

    df = pandas.DataFrame(
        data, columns=[
            'Название услуги',
        ],
    )

    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)
    return buffer.getvalue()


def get_jobs_fp_xlsx(
        xlsx_file: bytes,
) -> list[dict]:
    df = pandas.read_excel(BytesIO(xlsx_file))

    jobs_fp = []
    for index, job_name in enumerate(df.values):
        jobs_fp.append(
            {"id": index + 1, "name": job_name[0]}
        )

    return jobs_fp
