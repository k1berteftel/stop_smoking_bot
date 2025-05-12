import datetime
from aiogram import Bot
from aiogram.types import CallbackQuery, User, Message, InlineKeyboardMarkup, InlineKeyboardButton, ContentType
from aiogram.fsm.context import FSMContext
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.api.entities import MediaAttachment
from aiogram_dialog.widgets.kbd import Button, Select
from aiogram_dialog.widgets.input import ManagedTextInput, MessageInput
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from utils.ai_funcs import clear_chat_history as rm_history, set_chat_history, transfer_context
from prompts.funcs import get_current_prompt
from utils.schdulers import send_messages
from utils.build_ids import get_random_id
from database.action_data_class import DataInteraction
from database.model import DeeplinksTable, AdminsTable
from config_data.config import load_config, Config
from states.state_groups import startSG, adminSG


async def add_user_sub(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    user_id = dialog_manager.dialog_data.get('user_id')
    await session.update_user_sub(user_id)
    await clb.answer('Подписка была успешно выдана пользователю')
    await dialog_manager.switch_to(adminSG.user_condition_menu)


async def set_user_status(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    user_id = dialog_manager.dialog_data.get('user_id')
    user_ai = await session.get_user_ai(user_id)
    prompt = get_current_prompt(2)
    prices = await session.get_prices()
    assistant_id = await transfer_context(user_ai.assistant_id, user_ai.thread_id, prompt, prices.temperature)
    await set_chat_history(user_ai.thread_id)
    await session.set_user_ai_data(user_id, status=2, assistant_id=assistant_id)
    try:
        await clb.answer('Пользователю был установлен новый статус')
    except Exception:
        ...
    await dialog_manager.switch_to(adminSG.user_condition_menu)


async def clear_chat_history(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    user_id = dialog_manager.dialog_data.get('user_id')
    user_ai = await session.get_user_ai(user_id)
    state: FSMContext = dialog_manager.middleware_data.get('state')
    print(state)
    #await rm_history(thread_id=user_ai.thread_id)
    #await session.set_user_ai_data(user_id, status=1)
    await session.del_user(clb.from_user.id)
    await clb.answer('История сообщений была успешно почищена')
    dialog_manager.dialog_data.clear()
    await dialog_manager.switch_to(adminSG.start)


async def user_condition_menu_getter(dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    user_id = dialog_manager.dialog_data.get('user_id')
    user = await session.get_user(user_id)
    return {
        'status': user.AI.status,
        'sub': '✅Есть' if user.sub else '❌Отсутствует'
    }


async def get_user_id(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    try:
        user_id = int(text)
    except Exception:
        if not text.startswith('@'):
            await msg.answer('Значение должно быть числом, пожалуйста попробуйте снова')
            return
        user_id = text[1::]
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    if isinstance(user_id, int):
        user = await session.get_user(user_id)
    else:
        user = await session.get_user_by_username(user_id)
    if user is None:
        await msg.answer('Такого пользователя нету в базе данных бота, пожалуйста попробуйте снова')
        return
    if isinstance(user_id, str):
        user_id = user.user_id
    dialog_manager.dialog_data['user_id'] = user_id
    await dialog_manager.switch_to(adminSG.user_condition_menu)


async def get_counter(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    try:
        counter = int(text)
    except Exception:
        await msg.answer('Значение должно быть числом, пожалуйста попробуйте снова')
        return
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    await session.set_prices(count=counter)
    await dialog_manager.switch_to(adminSG.get_counter)


async def get_counter_getter(dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    prices = await session.get_prices()
    return {'counter': prices.count}


async def get_static(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    users = await session.get_users()
    active = 0
    entry = {
        'today': 0,
        'yesterday': 0,
        '2_day_ago': 0
    }
    activity = 0
    subs = 0
    statuses = {
        1: 0,
        2: 0,
        3: 0,
        4: 0
    }
    transitions = {
        'basic': {
            'users': 0,
            'subs': 0
        },
        'ref': {
            'users': 0,
            'subs': 0
        },
        'deeplink': {
            'users': 0,
            'subs': 0
        }
    }
    with open('Мониторинг.txt', 'a') as file:
        file.write(f'Статистика на {datetime.datetime.today().date()}\n\n')
    for user in users:
        if user.active:
            active += 1
        for day in range(0, 3):
            print(user.entry.date(), (datetime.datetime.today() - datetime.timedelta(days=day)).date())
            with open('Мониторинг.txt', 'a') as file:
                file.write(f'\t({day} день){user.entry.date()} {(datetime.datetime.today() - datetime.timedelta(days=day)).date()}\n')
            if user.entry.date() == (datetime.datetime.today() - datetime.timedelta(days=day)).date():
                if day == 0:
                    entry['today'] = entry.get('today') + 1
                elif day == 1:
                    entry['yesterday'] = entry.get('yesterday') + 1
                else:
                    entry['2_day_ago'] = entry.get('2_day_ago') + 1
        if user.activity.date() > (datetime.datetime.today() - datetime.timedelta(days=1)).date():
            activity += 1
        if user.sub:
            subs += 1
        if not user.join and not user.referral and user.active:
            transitions['basic']['users'] += 1
            if user.sub:
                transitions['basic']['subs'] += 1
        if user.referral and user.active:
            transitions['ref']['users'] += 1
            if user.sub:
                transitions['ref']['subs'] += 1
        if user.join and user.active:
            transitions['deeplink']['users'] += 1
            if user.sub:
                transitions['deeplink']['sub'] += 1
        if not user.active:
            continue
        statuses[user.AI.status] = statuses.get(user.AI.status) + 1

    text = (
        f'<b>Статистика на {datetime.datetime.today().strftime("%d-%m-%Y")}</b>\n\nВсего пользователей: {len(users)}'
        f'\n - Активные пользователи(не заблокировали бота): {active}\n - Пользователей заблокировали '
        f'бота: {len(users) - active}\n - Провзаимодействовали с ботом за последние 24 часа: {activity}'
        f'\n - Пользователей с подпиской: {subs}\n\n'
        f'<b>Прирост аудитории:</b>\n - За сегодня: +{entry.get("today")}\n - Вчера: +{entry.get("yesterday")}'
        f'\n - Позавчера: + {entry.get("2_day_ago")}\n\n<b>Прогресс лечения:</b>\n - Новых: {statuses.get(1)}\n'
        f' - В работе(готов): {statuses.get(2)}\n - Бросило: {statuses.get(3)}\n - Срывов: {statuses.get(4)}'
        f'\n\n<b>Статистика по переходам:</b>\nОбычные переходы: {transitions["basic"]["users"]}/{transitions["basic"]["subs"]}'
        f'\nРеферальные переходы: {transitions["ref"]["users"]}/{transitions["ref"]["subs"]}\nПереходы по диплинкам: '
        f'{transitions["deeplink"]["users"]}/{transitions["deeplink"]["subs"]}'
    )
    await clb.message.answer(text)


async def text_choose(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    dialog_manager.dialog_data['text'] = clb.data.split('_')[0]
    await dialog_manager.switch_to(adminSG.get_ru_text)


async def ru_text_getter(dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    text = dialog_manager.dialog_data.get('text')
    texts = await session.get_text(text + '_ru')
    return {'text': texts}


async def get_ru_text(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    dialog_manager.dialog_data['text_ru'] = text
    await dialog_manager.switch_to(adminSG.get_en_text)


async def en_text_getter(dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    text = dialog_manager.dialog_data.get('text')
    texts = await session.get_text(text + '_en')
    return {'text': texts}


async def get_en_text(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    dialog_manager.dialog_data['text_en'] = text
    await dialog_manager.switch_to(adminSG.get_text_photo)


async def get_text_photo(msg: Message, widget: MessageInput, dialog_manager: DialogManager):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    column = dialog_manager.dialog_data.get('text')
    datas = {
        column + '_ru': dialog_manager.dialog_data.get('text_ru'),
        column + '_en': dialog_manager.dialog_data.get('text_en'),
        column + '_photo': msg.photo[-1].file_id
    }
    await session.set_texts(**datas)
    await msg.answer('Новые текста с фото были успешно сохранены')
    dialog_manager.dialog_data.clear()
    await dialog_manager.switch_to(adminSG.texts_menu)


async def no_photo_text_switcher(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    column = dialog_manager.dialog_data.get('text')
    datas = {
        column + '_ru': dialog_manager.dialog_data.get('text_ru'),
        column + '_en': dialog_manager.dialog_data.get('text_en'),
        column + '_photo': None
    }
    await session.set_texts(**datas)
    await clb.message.answer('Новые текста были успешно сохранены')
    dialog_manager.dialog_data.clear()
    await dialog_manager.switch_to(adminSG.texts_menu)


async def temperature_menu_getter(dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    prices = await session.get_prices()
    return {'temperature': prices.temperature}


async def get_temperature(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    try:
        temperature = float(text)
    except Exception:
        await msg.answer('Значение должно быть числом, пожалуйста попробуйте снова')
        return
    if not (0 < temperature < 1):
        await msg.answer('Число должно быть в диапозоне от 0 до 1, пожалуйста попробуйте еще раз')
        return
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    await session.set_prices(temperature=temperature)
    await dialog_manager.switch_to(adminSG.temperature_menu)


async def get_prompt_file(msg: Message, widget: MessageInput, dialog_manager: DialogManager):
    bot: Bot = dialog_manager.middleware_data.get('bot')
    prompt = dialog_manager.dialog_data.get('prompt')
    file = await bot.get_file(msg.document.file_id)
    if prompt == 'new':
        await bot.download_file(file.file_path, 'prompts/Новый.txt')
    elif prompt == 'abstract':
        await bot.download_file(file.file_path, 'prompts/Конспект.txt')
    else:
        await bot.download_file(file.file_path, 'prompts/Другое.txt')
    await msg.answer('Промпт был успешно обновлен')
    dialog_manager.dialog_data.clear()
    await dialog_manager.switch_to(adminSG.prompts_menu)


async def choosen_prompt_menu_getter(dialog_manager: DialogManager, **kwargs):
    prompt = dialog_manager.dialog_data.get('prompt')
    if prompt == 'new':
        media = MediaAttachment(type=ContentType.DOCUMENT, path='prompts/Новый.txt')
    elif prompt == 'abstract':
        media = MediaAttachment(type=ContentType.DOCUMENT, path='prompts/Конспект.txt')
    else:
        media = MediaAttachment(type=ContentType.DOCUMENT, path='prompts/Другое.txt')
    return {'media': media}


async def prompt_choose(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    dialog_manager.dialog_data['prompt'] = clb.data.split('_')[0]
    await dialog_manager.switch_to(adminSG.choosen_prompt_menu)


async def get_column_amount(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    try:
        amount = int(text)
    except Exception:
        await msg.answer('Значение должно быть числом, пожалуйста попробуйте снова')
        return
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    column: str = dialog_manager.dialog_data.get('column')
    data = {
        column + '_price': amount
    }
    await session.set_prices(**data)
    await dialog_manager.switch_to(adminSG.prices_menu)


async def price_menu_getter(dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    prices = await session.get_prices()
    return {
        'sub_price': prices.sub_price,
        'ref_price': prices.ref_price,
        'sub_ref_price': prices.sub_ref_price
    }


async def prises_switcher(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    if clb.data.startswith('subref'):
        dialog_manager.dialog_data['column'] = 'sub_ref'
    else:
        dialog_manager.dialog_data['column'] = clb.data.split('_')[0]
    await dialog_manager.switch_to(adminSG.get_amount)


async def voucher_menu_getter(dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    vouchers = await session.get_vouchers()
    text = ''
    for voucher in vouchers:
        text += f'{voucher.code} - {voucher.amount} месяцев - {voucher.inputs} вождений\n'
    return {
        'codes': text
    }


async def get_voucher_amount(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    try:
        amount = int(text)
    except Exception:
        await msg.answer('Введенные данные должны быть числом, пожалуйста попробуйте снова')
        return
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    code = dialog_manager.dialog_data.get('code')
    await session.add_voucher(code, amount)
    await dialog_manager.switch_to(adminSG.vouchers_menu)


async def get_voucher_kod(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    dialog_manager.dialog_data['code'] = text
    await dialog_manager.switch_to(adminSG.get_voucher_amount)


async def del_voucher_menu_getter(dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    vouchers = await session.get_vouchers()
    buttons = []
    for voucher in vouchers:
        buttons.append((f'{voucher.code} - {voucher.inputs}', voucher.id))
    return {
        'items': buttons
    }


async def del_voucher(clb: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: str):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    await session.del_voucher(int(item_id))
    await clb.answer('Данный код ваучера был успешно удален')


async def deeplink_menu_getter(dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    links: list[DeeplinksTable] = await session.get_deeplinks()
    text = ''
    for link in links:
        users = await session.get_users_by_join_link(link.link)
        active = 0
        today = 0
        activity = 0
        subs = 0
        for user in users:
            if user.active:
                active += 1
            if user.entry > datetime.datetime.today() - datetime.timedelta(days=1):
                today += 1
            if user.activity > datetime.datetime.today() - datetime.timedelta(days=1):
                activity += 1
            if user.sub:
                subs += 1
        text += (f'({link.name})https://t.me/AiStopSmoking_bot?start={link.link}: {link.entry}\nЗашло: {len(users)}'
                 f', активных: {active}, зашло сегодня: {today}, приобрели подписку: {subs}, активны в последние 24 часа: {activity}\n')
    count = 0
    active = 0
    today = 0
    activity = 0
    subs = 0
    for user in await session.get_users():
        if not user.join:
            count += 1
            if user.active:
                active += 1
            if user.entry > datetime.datetime.today() - datetime.timedelta(days=1):
                today += 1
            if user.activity > datetime.datetime.today() - datetime.timedelta(days=1):
                activity += 1
            if user.sub:
                subs += 1
    text_2 = (f'\n\nСтатистика без диплинков:\nактивных: {active}, зашло сегодня: {today}, приобрели подписку: {subs}, '
              f'активны в последние 24 часа: {activity}\n')
    return {
        'links': text + text_2,
        'joins': count
    }


async def get_deeplink_name(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    await session.add_deeplink(name=text, link=get_random_id())
    await dialog_manager.switch_to(adminSG.deeplink_menu)


async def del_deeplink(clb: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: str):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    await session.del_deeplink(item_id)
    await clb.answer('Ссылка была успешно удаленна')
    await dialog_manager.switch_to(adminSG.deeplink_menu)


async def del_deeplink_getter(dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    links: list[DeeplinksTable] = await session.get_deeplinks()
    buttons = []
    for link in links:
        buttons.append((f'({link.name}){link.link}: {link.entry}', link.link))
    return {'items': buttons}


async def del_admin(clb: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: str):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    await session.del_admin(int(item_id))
    await clb.answer('Админ был успешно удален')
    await dialog_manager.switch_to(adminSG.admin_menu)


async def admin_del_getter(dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    admins: list[AdminsTable] = await session.get_admins()
    buttons = []
    for admin in admins:
        buttons.append((admin.name, admin.user_id))
    return {'items': buttons}


async def refresh_url(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    id: str = dialog_manager.dialog_data.get('link_id')
    dialog_manager.dialog_data.clear()
    await session.del_link(id)
    await dialog_manager.switch_to(adminSG.admin_add)


async def admin_add_getter(dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    id = get_random_id()
    dialog_manager.dialog_data['link_id'] = id
    await session.add_link(id)
    return {'id': id}


async def admin_menu_getter(dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    admins: list[AdminsTable] = await session.get_admins()
    text = ''
    for admin in admins:
        text += f'{admin.name}\n'
    return {'admins': text}


async def get_mail(msg: Message, widget: MessageInput, dialog_manager: DialogManager):
    dialog_manager.dialog_data['message'] = [msg.message_id, msg.chat.id]
    await dialog_manager.switch_to(adminSG.get_time)


async def get_time(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    try:
        time = datetime.datetime.strptime(text, '%H:%M %d.%m')
    except Exception as err:
        print(err)
        await msg.answer('Вы ввели данные не в том формате, пожалуйста попробуйте снова')
        return
    dialog_manager.dialog_data['time'] = text
    await dialog_manager.switch_to(adminSG.get_keyboard)


async def get_mail_keyboard(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    try:
        buttons = text.split('\n')
        keyboard: list[tuple] = [(i.split('-')[0], i.split('-')[1]) for i in buttons]
    except Exception as err:
        print(err)
        await msg.answer('Вы ввели данные не в том формате, пожалуйста попробуйте снова')
        return
    dialog_manager.dialog_data['keyboard'] = keyboard
    await dialog_manager.switch_to(adminSG.confirm_mail)


async def cancel_malling(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    dialog_manager.dialog_data.clear()
    await dialog_manager.switch_to(adminSG.start)


async def start_malling(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    bot: Bot = dialog_manager.middleware_data.get('bot')
    scheduler: AsyncIOScheduler = dialog_manager.middleware_data.get('scheduler')
    time = dialog_manager.dialog_data.get('time')
    message = dialog_manager.dialog_data.get('message')
    keyboard = dialog_manager.dialog_data.get('keyboard')
    if keyboard:
        keyboard = [InlineKeyboardButton(text=i[0], url=i[1]) for i in keyboard]
    users = await session.get_users()
    if not time:
        for user in users:
            try:
                await bot.copy_message(
                    chat_id=user.user_id,
                    from_chat_id=message[1],
                    message_id=message[0],
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[keyboard]) if keyboard else None
                )
                if user.active == 0:
                    await session.set_active(user.user_id, 1)
            except Exception as err:
                print(err)
                await session.set_active(user.user_id, 0)
        await clb.answer('Рассылка прошла успешно')
    else:
        date = datetime.datetime.strptime(time, '%H:%M %d.%m')
        date = date.replace(year=datetime.datetime.today().year)
        scheduler.add_job(
            func=send_messages,
            args=[bot, session, InlineKeyboardMarkup(inline_keyboard=[keyboard]) if keyboard else None, message],
            next_run_time=date
        )
    await dialog_manager.switch_to(adminSG.start)


