import logging
import datetime
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject, User
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from utils.date_utils import get_touch_date
from utils.translator.translator import Translator
from utils.schdulers import remind_user_ai
from database.action_data_class import DataInteraction
from config_data.config import load_config, Config

config: Config = load_config()
logger = logging.getLogger(__name__)


class RemindMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user: User = data.get('event_from_user')

        if user is None:
            return await handler(event, data)
        scheduler: AsyncIOScheduler = data.get('scheduler')
        job = scheduler.get_job(job_id=f'remind_{user.id}')
        if job:
            job.remove()
        session: DataInteraction = data.get('session')
        translator: Translator = data.get('translator')
        db_user = await session.get_user(user.id)
        if not db_user:
            await session.add_user(user_id=user.id,
                                   username=user.username if user.username else '-',
                                   name=user.full_name, referral=None, sub_referral=None,
                                   join=None)
            #await session.set_locale(user.id, 'ru')
        await session.set_activity(user_id=user.id)
        result = await handler(event, data)
        bot: Bot = data.get('bot')

        date = await get_touch_date(user.id, session)
        if isinstance(date, list):
            for date in date:
                scheduler.add_job(
                    func=remind_user_ai,
                    args=[user.id, bot, session, translator, scheduler],
                    next_run_time=date
                )
        else:
            try:
                scheduler.add_job(
                    func=remind_user_ai,
                    args=[user.id, bot, session, translator, scheduler],
                    id=f'remind_{user.id}',
                    next_run_time=date
                )
            except Exception:
                ...
        return result



