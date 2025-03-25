from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from utils.translator.translator import Translator


async def get_only_vip_keyboard(translator: Translator) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=translator['sub_button'], callback_data='start_vip_dialog')]
        ]
    )
    return keyboard