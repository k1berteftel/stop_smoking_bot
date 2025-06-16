import asyncio
import uuid
from aiogram import Bot
from aiogram.types import (CallbackQuery, User, Message, LabeledPrice, InlineKeyboardButton,
                           InlineKeyboardMarkup, ContentType, ReplyKeyboardMarkup, KeyboardButton)
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram_dialog.widgets.kbd import Button, Select
from aiogram_dialog.widgets.input import ManagedTextInput
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from yookassa import Payment, Configuration, Payout

from utils.prices_funcs import get_usdt_rub
from utils.ai_funcs import get_assistant_and_thread, get_text_answer
from prompts.funcs import get_current_prompt
from utils.schdulers import check_payment
from utils.translator.translator import Translator
from database.action_data_class import DataInteraction
from config_data.config import load_config, Config
from states.state_groups import startSG


Configuration.account_id = 286317
Configuration.secret_key = 'live_ZWfufpazd2XRr68N5w8U6gLel2YnN4CQXFyPlJWXPN0'

config: Config = load_config()


async def start_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    admins = [user.user_id for user in await session.get_admins()]
    translator: Translator = dialog_manager.middleware_data.get('translator')
    user = await session.get_user(event_from_user.id)
    media_id = MediaId(file_id='AgACAgIAAxkBAAIHymf6rE2IUtTRhaBL9ZNgDDC6hntsAAKt7DEbLfjYS4O6Klscz1uzAQADAgADeQADNgQ')
    media = MediaAttachment(file_id=media_id, type=ContentType.PHOTO)
    admin = False
    if event_from_user.id in config.bot.admin_ids or event_from_user in admins:
        admin = True
    return {
        'text': translator['menu'],
        'ref': translator['ref_button'],
        'sub': translator['sub_button'],
        'info': translator['info_button'],
        'switch': translator['on_malling_button'] if not user.malling else translator['off_malling_button'],
        'close': translator['close_button'],
        'media': media,
        'admin': admin
    }


async def malling_toggle(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    user = await session.get_user(clb.from_user.id)
    await session.set_malling_status(clb.from_user.id, not user.malling if user.malling else True)
    await dialog_manager.switch_to(startSG.start)


async def close_dialog(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    await dialog_manager.done()
    await clb.message.delete()


async def get_voucher(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    translator: Translator = dialog_manager.middleware_data.get('translator')
    await msg.delete()
    if await session.check_voucher(msg.from_user.id, text):
        voucher = await session.get_voucher(text)
        if voucher.percent is not None and voucher.percent != 100:
            dialog_manager.dialog_data['percent'] = voucher.percent
            await dialog_manager.switch_to(startSG.rub_payment_menu)
            return
        await session.set_sub_end(msg.from_user.id, voucher.amount)
        await msg.answer(translator['success_voucher_notification'])
        keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='📍Меню')]], resize_keyboard=True)
        message = await msg.answer(translator['writing_action'])
        await msg.bot.send_chat_action(
            chat_id=msg.from_user.id,
            action='typing'
        )
        user_ai = await session.get_user_ai(msg.from_user.id)
        assistant_id, thread_id = user_ai.assistant_id, user_ai.thread_id
        if not assistant_id or not thread_id:
            role = get_current_prompt(user_ai.status)
            prices = await session.get_prices()
            assistant_id, thread_id = await get_assistant_and_thread(role, prices.temperature)
            await session.set_user_ai_data(msg.from_user.id, assistant_id=assistant_id, thread_id=thread_id)
        answer = await get_text_answer(translator['start_ai'], assistant_id, thread_id)
        await session.set_user_ai_data(msg.from_user.id, count=user_ai.count + 1)
        if isinstance(answer, str):
            print(answer)
            await msg.answer(answer, reply_markup=keyboard)
            await message.delete()
            await dialog_manager.done()
            await msg.delete()
            return
        await msg.answer(answer.get('answer'), reply_markup=keyboard)
        await message.delete()
        await dialog_manager.done()
        #await dialog_manager.switch_to(startSG.sub_menu)
    else:
        await msg.answer(translator['no_voucher_notification'])


async def get_voucher_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    translator: Translator = dialog_manager.middleware_data.get('translator')
    return {
        'text': translator['voucher'],
        'back': translator['back'],
    }


async def sub_menu_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    translator: Translator = dialog_manager.middleware_data.get('translator')
    user = await session.get_user(event_from_user.id)
    texts = await session.get_texts()
    media = False
    if user.locale == 'ru':
        text = texts.sub_ru + '\n\n' + (translator['sub'].format(
            sub=((translator['sub_widget'] + translator['sub_trial_widget'].format(
                date=user.sub_end.strftime('%d-%m-%Y'))
            ) if user.sub_end else translator['sub_widget'])
            if user.sub else translator['no_sub_widget'])
        )
    else:
        text = texts.sub_en + '\n\n' + (translator['sub'].format(
            sub=((translator['sub_widget'] + translator['sub_trial_widget'].format(
                date=user.sub_end.strftime('%d-%m-%Y'))
            ) if user.sub_end else translator['sub_widget'])
            if user.sub else translator['no_sub_widget'])
        )
    if texts.sub_photo:
        media = MediaId(file_id=texts.sub_photo)
        media = MediaAttachment(type=ContentType.PHOTO, file_id=media)
    return {
        'text': text,
        'media': media,
        'rub': translator['rub_button'],
        'stars': translator['stars_button'],
        'ton': translator['ton_button'],
        'voucher': translator['voucher_button'],
        'back': translator['back'],
        'ru': user.locale == 'ru',
        'en': user.locale == 'en'
    }


async def choose_payment(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    translator: Translator = dialog_manager.middleware_data.get('translator')
    pay_type = clb.data.split('_')[0]
    if pay_type == 'rub':
        await dialog_manager.switch_to(startSG.rub_payment_menu)
    elif pay_type == 'stars':
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=translator['payment_button'], pay=True)],
                [InlineKeyboardButton(text=translator['back'], callback_data='back|sub_menu')]
            ]
        )
        await dialog_manager.done()
        await clb.message.delete()
        price = int(round((await session.get_prices()).sub_price / 1.7, 0))
        prices = [LabeledPrice(label="XTR", amount=price)]
        await clb.message.answer_invoice(
            title=translator['payment_widget'],
            description=translator['payment_widget'],
            prices=prices,
            provider_token="",
            payload="sub_payment",
            currency="XTR",
            reply_markup=keyboard
        )
    else:
        pass


async def rub_payment_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    scheduler: AsyncIOScheduler = dialog_manager.middleware_data.get('scheduler')
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    translator: Translator = dialog_manager.middleware_data.get('translator')
    percent = dialog_manager.dialog_data.get('percent')
    price = (await session.get_prices()).sub_price
    if percent:
        price = price * (1 - (percent / 100))
    bot: Bot = dialog_manager.middleware_data.get('bot')
    payment = await Payment.create({
        "amount": {
            "value": str(float(price)),
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/AiStopSmoking_bot"
        },
        "receipt": {
            "customer": {
                "email": "kkulis985@gmail.com"
            },
            'items': [
                {
                    'description': "Приобретение подписки",
                    "amount": {
                        "value": str(float(price)),
                        "currency": "RUB"
                    },
                    'vat_code': 1,
                    'quantity': 1
                }
            ]
        },
        "capture": True,
        "description": "Приобретение подписки"
    }, uuid.uuid4())
    url = payment.confirmation.confirmation_url
    scheduler.add_job(
        check_payment,
        'interval',
        args=[payment.id, event_from_user.id, bot, scheduler, session, translator],
        kwargs={'amount': price},
        id=f'payment_{event_from_user.id}',
        seconds=5
    )
    return {
        'text': translator['rub_widget'],
        'payment': translator['payment_button'],
        'back': translator['back'],
        'url': url
    }


async def close_rub_payment(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    scheduler: AsyncIOScheduler = dialog_manager.middleware_data.get('scheduler')
    job = scheduler.get_job(job_id=f'payment_{clb.from_user.id}')
    if job:
        job.remove()
    await dialog_manager.switch_to(startSG.start, show_mode=ShowMode.DELETE_AND_SEND)


async def ref_menu_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    translator: Translator = dialog_manager.middleware_data.get('translator')
    user = await session.get_user(event_from_user.id)
    texts = await session.get_texts()
    media = False
    if user.locale == 'ru':
        ref_text = texts.ref_ru
    else:
        ref_text = texts.ref_en

    if user.sub:
        text = ref_text + translator['ref'].format(refs=user.refs, sub_refs=user.sub_refs, balance=user.balance.rub,
                                         user_id=user.user_id)
    else:
        text = ref_text + translator['ref_no_sub']
    if texts.ref_photo:
        media = MediaId(file_id=texts.ref_photo)
        media = MediaAttachment(type=ContentType.PHOTO, file_id=media)
    return {
        'text': text,
        'media': media,
        'derive': translator['derive_button'],
        'share': translator['share_button'],
        'user_id': user.user_id,
        'back': translator['back'],
        'sub': user.sub
    }


async def get_derive_amount_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    translator: Translator = dialog_manager.middleware_data.get('translator')
    return {
        'text': translator['derive'],
        'back': translator['back']
    }


async def get_derive_amount(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    translator: Translator = dialog_manager.middleware_data.get('translator')
    await msg.delete()
    try:
        amount = int(text)
    except Exception:
        await msg.answer(translator['derive_integer_warning'])
        return
    user = await session.get_user(msg.from_user.id)
    if amount > user.balance.rub:
        await msg.answer(translator['derive_enough_warning'])
        return
    dialog_manager.dialog_data['amount'] = amount
    await dialog_manager.switch_to(startSG.get_derive_card)


async def get_derive_card_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    translator: Translator = dialog_manager.middleware_data.get('translator')
    return {
        'text': translator['derive_card'],
        'back': translator['back']
    }


async def get_derive_card(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    translator: Translator = dialog_manager.middleware_data.get('translator')
    await msg.delete()
    await msg.answer(translator['start_money_transfer'])
    amount = dialog_manager.dialog_data.get("amount")
    user = await session.get_user(msg.from_user.id)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Подтвердить перевод', callback_data=f'confirm_{msg.from_user.id}')],
            [InlineKeyboardButton(text='Отклонить', callback_data=f'decline_{msg.from_user.id}')]
        ]
    )
    if not await session.add_application(msg.from_user.id, amount):
        await msg.answer(translator['one_application_warning'])
        dialog_manager.dialog_data.clear()
        await dialog_manager.switch_to(startSG.ref_menu)
        return
    await msg.bot.send_message(
        chat_id=config.bot.admin_ids[0],
        text=f'Заявка на вывод средств. Данные по заявке:\n - Юзернейм: @{user.username}\n - Сумма для вывода: {amount}'
             f'Руб\n - Реквизиты для вывода: {text}',
        reply_markup=keyboard
    )
    dialog_manager.dialog_data.clear()
    await dialog_manager.switch_to(startSG.ref_menu)


async def info_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    translator: Translator = dialog_manager.middleware_data.get('translator')
    user = await session.get_user(event_from_user.id)
    texts = await session.get_texts()
    media = False
    if user.locale == 'ru':
        info_text = texts.info_ru
    else:
        info_text = texts.info_en
    if texts.info_photo:
        media = MediaId(file_id=texts.info_photo)
        media = MediaAttachment(type=ContentType.PHOTO, file_id=media)
    return {
        'text': info_text,
        'media': media,
        'back': translator['back']
    }
