import asyncio
from aiogram import Bot
from yookassa import Configuration, Payment
from yookassa.payment import PaymentResponse
from aiogram import Bot
from aiogram_dialog import DialogManager
from aiogram.types import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from utils.ai_funcs import get_assistant_and_thread
from prompts.funcs import get_current_prompt
from utils.date_utils import get_touch_date
from utils.ai_funcs import get_text_answer
from utils.translator.translator import Translator
from database.action_data_class import DataInteraction


async def send_messages(bot: Bot, session: DataInteraction, keyboard: InlineKeyboardMarkup|None, message: list[int]):
    users = await session.get_users()
    for user in users:
        try:
            await bot.copy_message(
                chat_id=user.user_id,
                from_chat_id=message[1],
                message_id=message[0],
                reply_markup=keyboard
            )
            if user.active == 0:
                await session.set_active(user.user_id, 1)
        except Exception as err:
            print(err)
            await session.set_active(user.user_id, 0)


async def check_payment(payment_id: any, user_id: int, bot: Bot, scheduler: AsyncIOScheduler,
                        session: DataInteraction, translator: Translator, **kwargs):
    payment: PaymentResponse = await Payment.find_one(payment_id)
    if payment.paid:
        amount = kwargs.get('amount')
        user = await session.get_user(user_id)
        if user.sub_end:
            await session.set_sub_end(user_id, 12)
        await session.update_user_sub(user_id)
        prices = await session.get_prices()
        if user.referral:
            referral = await session.get_user(user.referral)
            rub = int(round(amount * prices.ref_price / 100))
            await session.update_user_balance(referral.user_id, rub, 'rub')
            await session.set_paid_referral(user.user_id)
            referrals = await session.get_user_refs(referral.user_id)
            count = 0
            for ref in referrals:
                if ref.paid_referral:
                    count += 1
            if count >= 2:
                await session.update_user_sub(referral.user_id)
        if user.sub_referral:
            sub_referral = await session.get_user(user.sub_referral)
            rub = int(round(amount * prices.sub_ref_price / 100))
            await session.update_user_balance(sub_referral.user_id, rub, 'rub')
        await bot.send_message(chat_id=user_id, text=translator['success_payment'])
        scheduler.remove_job(job_id=f'payment_{user_id}')
        message = await bot.send_message(chat_id=user_id, text=translator['writing_action'])
        await bot.send_chat_action(
            chat_id=user_id,
            action='typing'
        )
        keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='📍Меню')]], resize_keyboard=True)
        user_ai = await session.get_user_ai(user_id)
        assistant_id, thread_id = user_ai.assistant_id, user_ai.thread_id
        if not user_ai.assistant_id or not user_ai.thread_id:
            role = get_current_prompt(user_ai.status)
            prices = await session.get_prices()
            assistant_id, thread_id = await get_assistant_and_thread(role, prices.temperature)
            await session.set_user_ai_data(user_id, assistant_id=assistant_id, thread_id=thread_id)
        answer = await get_text_answer(translator['continue_ai'], assistant_id, thread_id)
        await session.set_user_ai_data(user_id, count=user_ai.count + 1)
        if isinstance(answer, str):
            print(answer)
            await bot.send_message(
                chat_id=user_id,
                text=answer,
                reply_markup=keyboard
            )
            await message.delete()
            return
        await bot.send_message(
            chat_id=user_id,
            text=answer.get('answer'),
            reply_markup=keyboard
        )
        await message.delete()
    return


async def remind_user_ai(user_id: int, bot: Bot, session: DataInteraction, translator: Translator, scheduler: AsyncIOScheduler):
    user_ai = await session.get_user_ai(user_id)
    assistant_id, thread_id = user_ai.assistant_id, user_ai.thread_id
    answer = await get_text_answer(translator['getting_touch_action'], assistant_id, thread_id)
    await session.set_user_ai_data(user_id, count=user_ai.count + 1)
    if isinstance(answer, str):
        print(answer)
        await bot.send_message(chat_id=user_id, text=answer)
        return
    await bot.send_message(chat_id=user_id, text=answer.get('answer'))
    job = scheduler.get_job(job_id=f'remind_{user_id}')
    if job:
        job.remove()
    date = await get_touch_date(user_id, session)
    if isinstance(date, list):
        for date in date:
            scheduler.add_job(
                func=remind_user_ai,
                args=[user_id, bot, session, translator, scheduler],
                next_run_time=date
            )
    else:
        scheduler.add_job(
            func=remind_user_ai,
            args=[user_id, bot, session, translator, scheduler],
            id=f'remind_{user_id}',
            next_run_time=date
        )
