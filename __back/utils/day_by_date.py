from datetime import datetime


def get_day_of_week_by_date(date):
    dt_obj = datetime.strptime(date, '%d.%m.%Y')
    week = ['ПОНЕДЕЛЬНИК', 'ВТОРНИК', 'СРЕДА', 'ЧЕТВЕРГ', 'ПЯТНИЦА', 'СУББОТА', 'ВОСКРЕСЕНЬЕ']
    return week[dt_obj.weekday()]
