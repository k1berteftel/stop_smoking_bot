from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, CommandObject, Command
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery
from aiogram_dialog import DialogManager, StartMode

from utils.prices_funcs import get_usdt_rub
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database.action_data_class import DataInteraction
from states import state_groups as states


payment_router = Router()


@payment_router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@payment_router.message(F.successful_payment)
async def success_payment(msg: Message, session: DataInteraction, translator: DataInteraction, dialog_manager: DialogManager):
    amount = int(round(msg.successful_payment.total_amount * 1.7))  # рубли
    user = await session.get_user(msg.from_user.id)
    course = await get_usdt_rub()  # курс рублей в долларе
    usdt = int(round(amount / course))
    await session.update_user_sub(user.user_id)
    prizes = await session.get_prices()
    if user.referral:
        referral = await session.get_user(user.referral)
        ton = int(round(usdt * prizes.ref_prize / 100))
        await session.update_user_balance(referral.user_id, ton, 'usdt')
    if user.sub_referral:
        sub_referral = await session.get_user(user.sub_referral)
        ton = int(round(usdt * prizes.sub_ref_prize / 100))
        await session.update_user_balance(sub_referral.user_id, ton, 'usdt')