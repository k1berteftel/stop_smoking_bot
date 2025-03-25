import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import select
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from cachetools import TTLCache

from database.action_data_class import DataInteraction
from database.model import UsersTable
from utils.translator import Translator

logger = logging.getLogger(__name__)


class TransferObjectsMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()
        self.cache = TTLCache(
            maxsize=1000,
            ttl=60 * 60 * 12,  # 12 часов
        )

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:

        user: User = data.get('event_from_user')

        if user is None:
            return await handler(event, data)

        user: User = data.get('event_from_user')

        if user is None:
            return await handler(event, data)

        sessions: async_sessionmaker = data.get('_session')
        if user.id not in self.cache:
            async with sessions() as session:
                person = await session.scalar(select(UsersTable).where(UsersTable.user_id == user.id))
            self.cache[user.id] = person
        else:
            person = self.cache.get(user.id)
        if not person or not person.locale:
            print('ru')
            locale = 'ru'
        else:
            locale = person.locale

        scheduler: AsyncIOScheduler = data.get('_scheduler')

        interaction = DataInteraction(sessions)
        translator = Translator(locale)
        data['translator'] = translator
        data['session'] = interaction
        data['scheduler'] = scheduler
        return await handler(event, data)