import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from database.action_data_class import DataInteraction

logger = logging.getLogger(__name__)


class TransferObjectsMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:

        user: User = data.get('event_from_user')

        if user is None:
            return await handler(event, data)

        sessions: async_sessionmaker = data.get('_session')

        interaction = DataInteraction(sessions)
        data['session'] = interaction
        return await handler(event, data)