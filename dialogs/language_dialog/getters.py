import datetime
from aiogram import Bot
from aiogram.types import CallbackQuery, User, Message, ContentType, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram_dialog.widgets.kbd import Button, Select
from aiogram_dialog.widgets.input import ManagedTextInput, MessageInput
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from utils.translator import Translator as create_translator
from utils.translator.translator import Translator
from utils.ai_funcs import get_assistant_and_thread, get_text_answer
from prompts.funcs import get_current_prompt
from database.action_data_class import DataInteraction


async def start_getter(dialog_manager: DialogManager, **kwargs):
    translator: Translator = dialog_manager.middleware_data.get('translator')
    return {
        'text': translator['language'],
        'back': translator['back'],
    }


async def language_toggle(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    locale = clb.data.split('_')[0]
    user = await session.get_user(clb.from_user.id)
    await session.set_locale(clb.from_user.id, locale)
    await dialog_manager.done()
    await clb.message.delete()
    if not user.locale:
        translator: Translator = create_translator(locale)
        user_ai = await session.get_user_ai(clb.from_user.id)
        if not user_ai.assistant_id or not user_ai.thread_id:
            role = get_current_prompt(user_ai.status)
            prices = await session.get_prices()
            assistant_id, thread_id = await get_assistant_and_thread(role, prices.temperature)
            await session.set_user_ai_data(clb.from_user.id, assistant_id=assistant_id, thread_id=thread_id)
            answer = await get_text_answer(translator['start_ai'], assistant_id, thread_id)
            await session.set_user_ai_data(clb.from_user.id, count=user_ai.count + 1)
            if isinstance(answer, str):
                print(answer)
                await clb.message.answer(answer)
                return
            await clb.message.answer(answer.get('answer'))
