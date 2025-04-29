from aiogram.fsm.state import State, StatesGroup

# Обычная группа состояний


class startSG(StatesGroup):
    start = State()
    sub_menu = State()
    rub_payment_menu = State()
    get_voucher = State()
    ref_menu = State()
    get_derive_amount = State()
    get_derive_card = State()
    info = State()


class languagesSG(StatesGroup):
    start = State()


class adminSG(StatesGroup):
    start = State()
    get_keyboard = State()
    get_mail = State()
    get_time = State()
    confirm_mail = State()
    deeplink_menu = State()
    get_deeplink_name = State()
    deeplink_del = State()
    admin_menu = State()
    admin_del = State()
    admin_add = State()
    vouchers_menu = State()
    get_voucher = State()
    get_voucher_amount = State()
    del_voucher = State()
    prices_menu = State()
    get_amount = State()
    prompts_menu = State()
    choosen_prompt_menu = State()
    temperature_menu = State()
    get_counter = State()
    texts_menu = State()
    get_ru_text = State()
    get_en_text = State()
    get_text_photo = State()
    condition_menu = State()
    user_condition_menu = State()
