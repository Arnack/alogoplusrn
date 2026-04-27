import re
from datetime import timedelta, datetime


async def extract_and_subtract_hour(time_string):
    time_pattern = r'(\d+)[.:]?(\d*)'

    match = re.search(time_pattern, time_string)

    if not match:
        return None

    hours = int(match.group(1))
    minutes = int(match.group(2)) if match.group(2) else 0

    dt_time = datetime.strptime(f"{hours}:{minutes}", "%H:%M")
    new_dt_time = dt_time - timedelta(hours=2)

    return new_dt_time.strftime("%H:%M")
