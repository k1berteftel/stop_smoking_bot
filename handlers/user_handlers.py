import datetime

from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, CommandObject, Command, and_f, StateFilter
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram_dialog import DialogManager, StartMode
from aiogram.fsm.context import FSMContext

from prompts.funcs import get_current_prompt
from keyboards.keyboard import get_only_vip_keyboard
from utils.ai_funcs import get_assistant_and_thread, get_text_answer, get_answer_by_prompt, transfer_context, assistant_messages_abstract, _get_chat_history, clear_chat_history
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database.action_data_class import DataInteraction
from utils.translator.translator import Translator
from utils.translator import Translator as create_translator
from utils.schdulers import bot_writing
from filters.custom_filter import MsgStateFilter
from states import state_groups as states


user_router = Router()


@user_router.message(CommandStart())
async def start_dialog(msg: Message, dialog_manager: DialogManager, session: DataInteraction, command: CommandObject, scheduler: AsyncIOScheduler):
    #  ___
    #user_ai = await session.get_user_ai(1236300146)
    #await clear_chat_history(user_ai.thread_id)
    #print(await _get_chat_history(user_ai.thread_id))
    #  ___
    keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='📍Меню')]], resize_keyboard=True)
    #text = 'Привет! Готов начать путь к здоровой жизни? Мы поможем тебе отказаться от курения. Давай вместе сделаем первый шаг!'
    #await msg.answer(text, reply_markup=keyboard)
    deeplink = None
    referral = None
    sub_referral = None
    args = command.args
    job = scheduler.get_job(job_id=f'payment_{msg.from_user.id}')
    if job:
        job.remove()
    if args:
        if not await session.check_user(msg.from_user.id):
            try:
                args = int(args)
                users = [user.user_id for user in await session.get_users()]
                if args in users:
                    referral = args
                    await session.add_refs(args)
                    user = await session.get_user(referral)
                    if user.referral:
                        sub_referral = user.referral
                        await session.add_sub_refs(sub_referral)
            except Exception:
                ...
        link_ids = await session.get_links()
        ids = [i.link for i in link_ids]
        if args in ids:
            await session.add_admin(msg.from_user.id, msg.from_user.full_name)
            await session.del_link(args)
        if not await session.check_user(msg.from_user.id):
            deeplinks = await session.get_deeplinks()
            deep_list = [i.link for i in deeplinks]
            if args in deep_list:
                deeplink = args
                await session.add_entry(args)
    if dialog_manager.has_context():
        await dialog_manager.done()
        try:
            await msg.bot.delete_message(chat_id=msg.from_user.id, message_id=msg.message_id - 1)
        except Exception:
            ...
    if not await session.check_user(msg.from_user.id):
        await session.add_user(user_id=msg.from_user.id,
                               username=msg.from_user.username if msg.from_user.username else '-',
                               name=msg.from_user.full_name, referral=referral, sub_referral=sub_referral, join=deeplink)
    #await dialog_manager.start(states.languagesSG.start, mode=StartMode.RESET_STACK)
    user = await session.get_user(msg.from_user.id)
    if not user.locale:
        await session.set_locale(msg.from_user.id, 'ru')
        translator: Translator = create_translator('ru')
        message = await msg.answer(translator['writing_action'])
        await msg.bot.send_chat_action(
            chat_id=msg.from_user.id,
            action='typing'
        )
        user_ai = await session.get_user_ai(msg.from_user.id)
        if not user_ai.assistant_id or not user_ai.thread_id:
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
                return
            await msg.answer(answer.get('answer'), reply_markup=keyboard)
            await message.delete()


@user_router.message(F.text == '📍Меню')
async def start_user_dialog(msg: Message, dialog_manager: DialogManager):
    if dialog_manager.has_context():
        await dialog_manager.done()
        try:
            await msg.bot.delete_message(chat_id=msg.from_user.id, message_id=msg.message_id - 1)
        except Exception:
            ...
    await dialog_manager.start(states.startSG.start, mode=StartMode.RESET_STACK)


@user_router.callback_query(F.data == 'start_vip_dialog')
async def start_vip_dialog(msg: Message, dialog_manager: DialogManager, state: FSMContext):
    await state.clear()
    if dialog_manager.has_context():
        await dialog_manager.done()
        try:
            await msg.bot.delete_message(chat_id=msg.from_user.id, message_id=msg.message_id - 1)
        except Exception:
            ...
    await dialog_manager.start(states.startSG.sub_menu, mode=StartMode.RESET_STACK)


#@user_router.message()
#async def get_photo_id(msg: Message):
    #print('pass')
    #await msg.reply(msg.photo[-1].file_id)


@user_router.message(MsgStateFilter())
async def answer_message(msg: Message, dialog_manager: DialogManager, state: FSMContext, session: DataInteraction, scheduler: AsyncIOScheduler, translator: Translator):
    if dialog_manager.has_context():
        await dialog_manager.done()
        try:
            await msg.bot.delete_message(chat_id=msg.from_user.id, message_id=msg.message_id - 1)
        except Exception:
            ...
    user = await session.get_user(msg.from_user.id)
    user_ai = await session.get_user_ai(msg.from_user.id)
    data = await state.get_data()
    prices = await session.get_prices()
    assistant_id, thread_id = user_ai.assistant_id, user_ai.thread_id#data.get('assistant_id'), data.get('thread_id')
    if not assistant_id or not thread_id:
        assistant_id, thread_id = user_ai.assistant_id, user_ai.thread_id
        if not assistant_id or not thread_id:
            role = get_current_prompt(user_ai.status)
            assistant_id, thread_id = await get_assistant_and_thread(role, prices.temperature)
            await session.set_user_ai_data(msg.from_user.id, assistant_id=assistant_id, thread_id=thread_id)
        await state.update_data(assistant_id=assistant_id, thread_id=thread_id)
    if user_ai.status != 1 and not user.sub:
        keyboard = await get_only_vip_keyboard(translator)
        #await msg.answer(
            #text=translator['only_vip_warning'],
            #reply_markup=keyboard
        #)
        await msg.answer_photo(
            photo='AgACAgIAAxkBAAIud2gX9LqFipbhoZw92X0xTterBXuTAAIVAzIbhhrBSDeTVUT3q5k1AQADAgADeQADNgQ',
            caption=translator['only_vip_warning'],
            reply_markup=keyboard
        )
        return
    if user.sub and user.sub_end and user.sub_end.timestamp() < datetime.datetime.today().timestamp():
        await session.set_sub_end(user_id=msg.from_user.id, months=None)
        keyboard = await get_only_vip_keyboard(translator)
        await msg.answer_photo(
            photo='AgACAgIAAxkBAAIud2gX9LqFipbhoZw92X0xTterBXuTAAIVAzIbhhrBSDeTVUT3q5k1AQADAgADeQADNgQ',
            caption=translator['only_vip_warning'],
            reply_markup=keyboard
        )
        return
    message = await msg.answer(translator['writing_action'])
    await msg.bot.send_chat_action(
        chat_id=msg.from_user.id,
        action='typing'
    )
    text = msg.text + f'\n\nСистемное время: {msg.date.strftime("%d-%m-%Y")}'
    answer = await get_text_answer(text, assistant_id, thread_id)
    #if user_ai.status != 1:
        #await session.set_user_ai_data(msg.from_user.id, count=user_ai.count + 1)
    print('user data: ', user_ai.count)
    if user_ai.count >= prices.count:
        await session.set_user_ai_data(msg.from_user.id, count=0)
        try:
            abstract = await assistant_messages_abstract(thread_id)
            print(abstract.content)
        except Exception as err:
            print(err)
        else:
            content = abstract.content.strip()
            try:
                await msg.answer('<b>Получившийся конспект:</b> \n\n', content)
            except Exception as error:
                print(error)
    if answer is None:
        await message.delete()
        await msg.answer('Что-то пошло не так, пожалуйста попробуйте снова')
        return
    keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='📍Меню')]], resize_keyboard=True)
    if isinstance(answer, str):
        await message.delete()
        print(answer)
        await msg.answer(answer, reply_markup=keyboard)
        return
    if user_ai.status != answer.get('user_status') and answer.get('user_status') > user_ai.status:
        prompt = get_current_prompt(answer.get('user_status'))
        print('start transfer')
        prices = await session.get_prices()
        assistant_id = await transfer_context(assistant_id, thread_id, prompt, prices.temperature)
        await session.set_user_ai_data(msg.from_user.id, assistant_id=assistant_id, status=answer.get('user_status'), count=0)
        await state.update_data(assistant_id=assistant_id)
    if answer.get('jobs'):
        jobs = answer.get('jobs')
        for job in jobs:
            if not job.get('description'):
                continue
            try:
                pass
                #date = datetime.datetime.strptime(job.get('time'), '%Y-%m-%d %H:%M:%S')
                #jobs = scheduler.get_jobs()
                #scheduler.add_job(
                    #bot_writing,
                    #args=[msg.from_user.id, msg.bot, session, job.get('description')],
                    #next_run_time=date
                #)
            except Exception as err:
                print('scheduler error', err)
                continue
    await message.delete()
    await msg.answer(answer.get('answer'), reply_markup=keyboard)
