from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import async_sessionmaker

from database.action_data_class import DataInteraction
from utils.schdulers import remind_user_ai
from utils.date_utils import get_touch_date
from utils.translator import Translator


async def start_schedulers(session: async_sessionmaker, scheduler: AsyncIOScheduler, bot: Bot):
    session = DataInteraction(session)
    users = await session.get_users()
    for user in users:
        if not user.AI:
            continue
        translator = Translator(user.locale)
        date = await get_touch_date(user.user_id, session)
        if isinstance(date, list):
            for date in date:
                scheduler.add_job(
                    func=remind_user_ai,
                    args=[user.id, bot, session, translator, scheduler],
                    next_run_time=date
                )
        else:
            scheduler.add_job(
                func=remind_user_ai,
                args=[user.id, bot, session, translator, scheduler],
                id=f'remind_{user.id}',
                next_run_time=date
            )