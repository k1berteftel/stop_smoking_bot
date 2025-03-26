import uuid
from aiogram import Bot
from aiogram.types import (CallbackQuery, User, Message, LabeledPrice, InlineKeyboardButton,
                           InlineKeyboardMarkup, ContentType)
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram_dialog.widgets.kbd import Button, Select
from aiogram_dialog.widgets.input import ManagedTextInput
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from yookassa import Payment, Configuration

from utils.prices_funcs import get_usdt_rub
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
    translator: Translator = dialog_manager.middleware_data.get('translator')
    media_id = MediaId(file_id='AgACAgIAAxkBAAM3Z-QLzEXIBU865pSSPn69jafliXQAAnD8MRummCFL-zpvZdAR1SEBAAMCAAN5AAM2BA')
    media = MediaAttachment(file_id=media_id, type=ContentType.PHOTO)
    admin = False
    if event_from_user.id in config.bot.admin_ids:
        admin = True
    return {
        'text': translator['menu'],
        'ref': translator['ref_button'],
        'sub': translator['sub_button'],
        'info': translator['info_button'],
        'close': translator['close_button'],
        'media': media,
        'admin': admin
    }


async def close_dialog(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    await dialog_manager.done()
    await clb.message.delete()


async def get_voucher(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    translator: Translator = dialog_manager.middleware_data.get('translator')
    await msg.delete()
    if await session.check_voucher(msg.from_user.id, text):
        amount = await session.get_voucher_amount(text)
        await session.set_trial_sub(msg.from_user.id, amount)
        await msg.answer(translator['success_voucher_notification'])
        await dialog_manager.switch_to(startSG.sub_menu)
    else:
        await msg.answer(translator['no_voucher_notification'])


async def get_voucher_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    translator: Translator = dialog_manager.middleware_data.get('translator')
    return {
        'text': translator['voucher'],
        'back': translator['back'],
    }


async def ref_menu_switcher(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    user = await session.get_user(clb.from_user.id)
    if not user.sub:
        translator: Translator = dialog_manager.middleware_data.get('translator')
        await clb.answer(translator['no_sub_warning'])
        return
    await dialog_manager.switch_to(startSG.ref_menu)


async def sub_menu_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    user = await session.get_user(event_from_user.id)
    texts = await session.get_texts()
    if user.locale == 'ru':
        sub_text = texts.sub_ru
    else:
        sub_text = texts.sub_en
    translator: Translator = dialog_manager.middleware_data.get('translator')
    return {
        'text': sub_text,
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
    price = (await session.get_prices()).sub_price
    bot: Bot = dialog_manager.middleware_data.get('bot')
    type = dialog_manager.dialog_data.get('type')
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
                    'description': "Приобретение генераций" if type == 'gen' else "Приобретение подписки",
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
        "description": "Приобретение генераций" if type == 'gen' else "Приобретение подписки"
    }, uuid.uuid4())
    url = payment.confirmation.confirmation_url
    scheduler.add_job(
        check_payment,
        'interval',
        args=[payment.id, event_from_user.id, bot, scheduler, session, translator],
        kwargs={'amount': dialog_manager.dialog_data.get('amount'), 'type': type},
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
    if user.locale == 'ru':
        ref_text = texts.ref_ru
    else:
        ref_text = texts.ref_en
    return {
        'text': ref_text + translator['ref'].format(refs=user.refs, sub_refs=user.sub_refs, balance=user.balance.rub,
                                         user_id=user.user_id),
        'derive': translator['derive_button'],
        'share': translator['share_button'],
        'user_id': user.user_id,
        'back': translator['back']
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
    try:
        card = int(''.join([card for card in text.strip().split(' ')]))
    except Exception:
        await msg.answer(translator['only_integer_card_warning'])
        return
    if len(str(card)) != 16:
        await msg.answer(translator['enough_card_len_warning'])
        return
    await msg.answer(translator['start_money_transfer'])



async def info_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    translator: Translator = dialog_manager.middleware_data.get('translator')
    user = await session.get_user(event_from_user.id)
    texts = await session.get_texts()
    if user.locale == 'ru':
        info_text = texts.info_ru
    else:
        info_text = texts.info_en
    return {
        'text': info_text,
        'back': translator['back']
    }
