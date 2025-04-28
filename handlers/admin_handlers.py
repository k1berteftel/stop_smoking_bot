import datetime

from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, CommandObject, Command
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram_dialog import DialogManager, StartMode
from aiogram.fsm.context import FSMContext

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database.action_data_class import DataInteraction
from utils.translator.translator import Translator
from utils.translator import Translator as create_translator


admin_router = Router()


@admin_router.callback_query(F.data.startswith('confirm'))
async def confirm_application(clb: CallbackQuery, session: DataInteraction):
    data = clb.data.split('_')
    user_id = int(data[-1])
    application = await session.get_application(user_id)
    if not application:
        await clb.message.delete()
        return
    amount: int = application.amount
    user = await session.get_user(user_id)
    translator = create_translator(user.locale)
    print(amount, -amount, sep='\t')
    await session.update_user_balance(user_id, -amount, 'rub')
    await clb.bot.send_message(text=translator['success_payout'], chat_id=user_id)
    await clb.answer('Заявка на вывод была успешно подтверждена')
    await session.del_application(user_id)
    await clb.message.delete()


@admin_router.callback_query(F.data.startswith('decline'))
async def decline_application(clb: CallbackQuery, session: DataInteraction):
    user_id = int(clb.data.split('_')[-1])
    user = await session.get_user(user_id)
    translator = create_translator(user.locale)
    await clb.bot.send_message(text=translator['unsuccess_payout'], chat_id=user_id)
    await clb.answer('Заявка была отклонена')
    await session.del_application(user_id)
    await clb.message.delete()