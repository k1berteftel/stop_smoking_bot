import datetime
from dateutil.relativedelta import relativedelta

from database.action_data_class import DataInteraction

time_range: list[int] = list(range(19, 25))
time_range.extend(range(0, 11))


async def get_touch_date(user_id: int, session: DataInteraction) -> datetime.datetime | list[datetime.datetime]:
    user_ai = await session.get_user_ai(user_id)
    if user_ai.status == 1:
        if (datetime.datetime.today() + datetime.timedelta(hours=12)).hour not in time_range:
            date = datetime.datetime.today() + datetime.timedelta(hours=12)
        else:
            date = await _get_current_differ(12)
    elif user_ai.status == 2:
        if (datetime.datetime.today() + datetime.timedelta(hours=5)).hour not in time_range:
            date = datetime.datetime.today() + datetime.timedelta(hours=5)
        else:
            date = await _get_current_differ(5)
    elif user_ai.status == 3:
        if user_ai.end_date.timestamp() > (datetime.datetime.today() - datetime.timedelta(days=3)).timestamp():
            if (datetime.datetime.today() + datetime.timedelta(hours=3)).hour not in time_range:
                date = datetime.datetime.today() + datetime.timedelta(hours=3)
            else:
                date = await _get_current_differ(3)
        elif (datetime.datetime.today() + datetime.timedelta(days=3)).timestamp() < user_ai.end_date.timestamp() < (
                datetime.datetime.today() + datetime.timedelta(days=7)).timestamp():
            if (datetime.datetime.today() + datetime.timedelta(hours=7)).hour not in time_range:
                date = datetime.datetime.today() + datetime.timedelta(hours=7)
            else:
                date = await _get_current_differ(7)
        elif (datetime.datetime.today() + datetime.timedelta(days=7)).timestamp() < user_ai.end_date.timestamp() < (
                datetime.datetime.today() + datetime.timedelta(days=30)).timestamp():
            date = await _get_current_dates()
        else:
            if datetime.datetime.today().hour not in time_range:
                date = datetime.datetime.today().replace(day=datetime.datetime.today().day + 3)
            else:
                for i in range(1, 14):
                    date = datetime.datetime.today().replace(hour=datetime.datetime.today().hour + i)
                    if date.hour not in time_range:
                        date = date + datetime.timedelta(days=3)
                        break

    return date
                        
                        
async def _get_current_differ(hours: int) -> datetime.datetime:
    today = datetime.datetime.today()
    if (today + datetime.timedelta(hours=hours)).hour not in time_range:
        return today + datetime.timedelta(hours=hours)
    else:
        if today.replace(hour=10).timestamp() < today.timestamp():
            return today.replace(hour=10) + datetime.timedelta(days=1)
        else:
            return today.replace(hour=10)


async def _get_current_dates() -> list[datetime.datetime]:
    today = datetime.datetime.today()
    dates = []
    morning_date = datetime.datetime(year=today.year, hour=10, minute=today.minute, day=today.day, month=today.month)
    evening_date = datetime.datetime(year=today.year, hour=19, minute=today.minute, day=today.day, month=today.month)
    if morning_date.timestamp() < today.timestamp():
        morning_date = morning_date + datetime.timedelta(days=1)
    if evening_date.timestamp() < today.timestamp():
        evening_date = evening_date + datetime.timedelta(days=1)
    dates.append(morning_date)
    dates.append(evening_date)
    return dates
