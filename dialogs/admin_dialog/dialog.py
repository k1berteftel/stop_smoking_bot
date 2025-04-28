from aiogram.types import ContentType
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import SwitchTo, Column, Row, Button, Group, Select, Start, Url, Cancel
from aiogram_dialog.widgets.text import Format, Const
from aiogram_dialog.widgets.input import TextInput, MessageInput
from aiogram_dialog.widgets.media import DynamicMedia

from dialogs.admin_dialog import getters
from states.state_groups import adminSG


admin_dialog = Dialog(
    Window(
        Const('Админ панель'),
        Button(Const('Получить статистику'), id='get_static', on_click=getters.get_static),
        SwitchTo(Const('Управление состояниями'), id='condition_menu_switcher', state=adminSG.condition_menu),
        SwitchTo(Const('Управление текстами'), id='texts_menu_switcher', state=adminSG.texts_menu),
        SwitchTo(Const('Управление температурой'), id='temperature_menu_switcher', state=adminSG.temperature_menu),
        SwitchTo(Const('Управление счетчиком до конспекта'), id='get_counter_switcher', state=adminSG.get_counter),
        SwitchTo(Const('Управление промптами'), id='prompts_menu_switcher', state=adminSG.prompts_menu),
        SwitchTo(Const('Управление кодами ваучера'), id='vouchers_menu', state=adminSG.vouchers_menu),
        SwitchTo(Const('🔗 Управление диплинками'), id='deeplinks_menu_switcher', state=adminSG.deeplink_menu),
        SwitchTo(Const('👥 Управление админами'), id='admin_menu_switcher', state=adminSG.admin_menu),
        SwitchTo(Const('Управление ценами и рефералкой'), id='prices_menu_switcher', state=adminSG.prices_menu),
        SwitchTo(Const('Сделать рассылку'), id='get_mail_switcher', state=adminSG.get_mail),
        Cancel(Const('Назад'), id='close_admin'),
        state=adminSG.start
    ),
    Window(
        Format('Действующее число сообщений до конспекта: {counter}, чтобы поменять его отправьте новое число'),
        TextInput(
            id='get_counter',
            on_success=getters.get_counter,
        ),
        SwitchTo(Const('🔙 Назад'), id='back', state=adminSG.start),
        getter=getters.get_counter_getter,
        state=adminSG.get_counter
    ),
    Window(
        Const('Введите User Id или Username пользователя , состояние которого надо поменять'),
        TextInput(
            id='get_user_id',
            on_success=getters.get_user_id
        ),
        SwitchTo(Const('🔙 Назад'), id='back', state=adminSG.start),
        state=adminSG.condition_menu
    ),
    Window(
        Const('Данные пользователя'),
        Format('Текущий статус: {status}\nПодписка: {sub}\n\n<em>Возможные статусы:'
               '\n - Новый(1)\n - Готов(2)\n - Бросил(3) \n - Срыв(4) </em>'),
        Column(
            Button(Const('Сбросить историю(сброс диалога)'), id='clear_chat_history', on_click=getters.clear_chat_history),
            Button(Const('Установить статус "готов"'), id='set_status_2', on_click=getters.set_user_status),
            Button(Const('Выдать подписку'), id='add_user_sub', on_click=getters.add_user_sub),
        ),
        SwitchTo(Const('🔙 Назад'), id='back_condition_menu', state=adminSG.condition_menu),
        getter=getters.user_condition_menu_getter,
        state=adminSG.user_condition_menu
    ),
    Window(
        Const('Меню управления текстами'),
        Column(
            Button(Const('"Информация"'), id='info_text_choose', on_click=getters.text_choose),
            Button(Const('"Подписка"'), id='sub_text_choose', on_click=getters.text_choose),
            Button(Const('"Рефералка"'), id='ref_text_choose', on_click=getters.text_choose),
        ),
        SwitchTo(Const('🔙 Назад'), id='back', state=adminSG.start),
        state=adminSG.texts_menu
    ),
    Window(
        Format('Действующий текст на русском:\n\n{text}\n\n\n'
               'Отправьте новый текст, чтобы поменять действующий'),
        TextInput(
            id='get_ru_text',
            on_success=getters.get_ru_text,
        ),
        SwitchTo(Const('🔙 Назад'), id='back_texts_menu', state=adminSG.texts_menu),
        getter=getters.ru_text_getter,
        state=adminSG.get_ru_text
    ),
    Window(
        Format('Действующий текст на анг:\n\n{text}\n\n\n'
               'Отправьте новый текст, чтобы поменять действующий'),
        TextInput(
            id='get_en_text',
            on_success=getters.get_en_text,
        ),
        getter=getters.en_text_getter,
        state=adminSG.get_en_text
    ),
    Window(
        Format('Действующая температура: {temperature}'),
        Const('Если хотите ее поменять отправьте число в диапозоне от 0 до 1'),
        TextInput(
            id='get_temperature',
            on_success=getters.get_temperature,
        ),
        SwitchTo(Const('🔙 Назад'), id='back', state=adminSG.start),
        getter=getters.temperature_menu_getter,
        state=adminSG.temperature_menu
    ),
    Window(
        Const('Меню управление промптами'),
        Column(
            Button(Const('"Новый"'), id='new_prompt_choose', on_click=getters.prompt_choose),
            Button(Const('"Готов и другое"'), id='ready_prompt_choose', on_click=getters.prompt_choose),
            Button(Const('Промпт конспекта'), id='abstract_prompt_choose', on_click=getters.prompt_choose),
        ),
        SwitchTo(Const('🔙 Назад'), id='back', state=adminSG.start),
        state=adminSG.prompts_menu
    ),
    Window(
        DynamicMedia('media'),
        Const('Отправьте новый файл с промптом'),
        MessageInput(
            getters.get_prompt_file,
            content_types=ContentType.DOCUMENT
        ),
        SwitchTo(Const('🔙 Назад'), id='back_prompts_menu', state=adminSG.prompts_menu),
        getter=getters.choosen_prompt_menu_getter,
        state=adminSG.choosen_prompt_menu
    ),
    Window(
        Format('Выберите то что вы хотели бы отредактировать\nЦена подписки: {sub_price}\n'
               'Процент с покупки реферала: {ref_price}%\nПроцент с покупки реферала второй ступени: {sub_ref_price}%'),
        Column(
            Button(Const('Цена подписки'), id='sub_price_choose', on_click=getters.prises_switcher),
            Button(Const('Процент с покупки реферала'), id='ref_prize_choose', on_click=getters.prises_switcher),
            Button(Const('Процент с покупки реферала второй ступени'), id='subref_prize_choose', on_click=getters.prises_switcher),
        ),
        SwitchTo(Const('🔙 Назад'), id='back', state=adminSG.start),
        getter=getters.price_menu_getter,
        state=adminSG.prices_menu
    ),
    Window(
        Const('Введите новое значение'),
        TextInput(
            id='get_column_amount',
            on_success=getters.get_column_amount
        ),
        SwitchTo(Const('🔙 Назад'), id='back_prices_menu', state=adminSG.prices_menu),
        state=adminSG.get_amount
    ),
    Window(
        Const('Меню управления кодами ваучера\n'),
        Format('Действующие коды:\n{codes}'),
        Column(
            SwitchTo(Const('Создать новый код'), id='get_voucher_kod_switcher', state=adminSG.get_voucher),
            SwitchTo(Const('Удалить существующий'), id='del_voucher_switcher', state=adminSG.del_voucher),
        ),
        SwitchTo(Const('🔙 Назад'), id='back', state=adminSG.start),
        getter=getters.voucher_menu_getter,
        state=adminSG.vouchers_menu
    ),
    Window(
        Const('Введите код ваучера'),
        TextInput(
            id='get_voucher_kod',
            on_success=getters.get_voucher_kod
        ),
        SwitchTo(Const('🔙 Назад'), id='back_voucher_menu', state=adminSG.vouchers_menu),
        state=adminSG.get_voucher
    ),
    Window(
        Const('Введите кол-во месяцев которое получит пользователь при вводе кода ваучера'),
        TextInput(
            id='get_voucher_amount',
            on_success=getters.get_voucher_amount
        ),
        SwitchTo(Const('🔙 Назад'), id='back_get_voucher', state=adminSG.get_voucher),
        state=adminSG.get_voucher_amount
    ),
    Window(
        Const('Выберите код ваучера который вы хотели бы удалить'),
        Group(
            Select(
                Format('{item[0]}'),
                id='voucher_del_builder',
                item_id_getter=lambda x: x[1],
                items='items',
                on_click=getters.del_voucher
            ),
            width=2
        ),
        SwitchTo(Const('🔙 Назад'), id='back_voucher_menu', state=adminSG.vouchers_menu),
        getter=getters.del_voucher_menu_getter,
        state=adminSG.del_voucher
    ),
    Window(
        Format('🔗 *Меню управления диплинками*\n\n'
               '🎯 *Имеющиеся диплинки*:\n{links}\nПереходов без диплинков: {joins}'),
        Column(
            SwitchTo(Const('➕ Добавить диплинк'), id='add_deeplink', state=adminSG.get_deeplink_name),
            SwitchTo(Const('❌ Удалить диплинки'), id='del_deeplinks', state=adminSG.deeplink_del),
        ),
        SwitchTo(Const('🔙 Назад'), id='back', state=adminSG.start),
        getter=getters.deeplink_menu_getter,
        state=adminSG.deeplink_menu
    ),
    Window(
        Const('Введите название ссылки'),
        TextInput(
            id='get_deeplink_name',
            on_success=getters.get_deeplink_name,
        ),
        SwitchTo(Const('🔙 Назад'), id='deeplinks_back', state=adminSG.deeplink_menu),
        state=adminSG.get_deeplink_name
    ),
    Window(
        Const('❌ Выберите диплинк для удаления'),
        Group(
            Select(
                Format('🔗 {item[0]}'),
                id='deeplink_builder',
                item_id_getter=lambda x: x[1],
                items='items',
                on_click=getters.del_deeplink
            ),
            width=1
        ),
        SwitchTo(Const('🔙 Назад'), id='deeplinks_back', state=adminSG.deeplink_menu),
        getter=getters.del_deeplink_getter,
        state=adminSG.deeplink_del
    ),
    Window(
        Format('👥 *Меню управления администраторами*\n\n {admins}'),
        Column(
            SwitchTo(Const('➕ Добавить админа'), id='add_admin_switcher', state=adminSG.admin_add),
            SwitchTo(Const('❌ Удалить админа'), id='del_admin_switcher', state=adminSG.admin_del)
        ),
        SwitchTo(Const('🔙 Назад'), id='back', state=adminSG.start),
        getter=getters.admin_menu_getter,
        state=adminSG.admin_menu
    ),
    Window(
        Const('👤 Выберите пользователя, которого хотите сделать админом\n'
              '⚠️ Ссылка одноразовая и предназначена для добавления только одного админа'),
        Column(
            Url(Const('🔗 Добавить админа (ссылка)'), id='add_admin',
                url=Format('http://t.me/share/url?url=https://t.me/AiStopSmoking_bot?start={id}')),  # поменять ссылку
            Button(Const('🔄 Создать новую ссылку'), id='new_link_create', on_click=getters.refresh_url),
            SwitchTo(Const('🔙 Назад'), id='back_admin_menu', state=adminSG.admin_menu)
        ),
        getter=getters.admin_add_getter,
        state=adminSG.admin_add
    ),
    Window(
        Const('❌ Выберите админа для удаления'),
        Group(
            Select(
                Format('👤 {item[0]}'),
                id='admin_del_builder',
                item_id_getter=lambda x: x[1],
                items='items',
                on_click=getters.del_admin
            ),
            width=1
        ),
        SwitchTo(Const('🔙 Назад'), id='back_admin_menu', state=adminSG.admin_menu),
        getter=getters.admin_del_getter,
        state=adminSG.admin_del
    ),
    Window(
        Const('Введите сообщение которое вы хотели бы разослать'),
        MessageInput(
            content_types=ContentType.ANY,
            func=getters.get_mail
        ),
        SwitchTo(Const('Назад'), id='back', state=adminSG.start),
        state=adminSG.get_mail
    ),
    Window(
        Const('Введите дату и время в которое сообщение должно отправиться всем юзерам в формате '
              'час:минута:день:месяц\n Например: 18:00 10.02 (18:00 10-ое февраля)'),
        TextInput(
            id='get_time',
            on_success=getters.get_time
        ),
        SwitchTo(Const('Продолжить без отложки'), id='get_keyboard_switcher', state=adminSG.get_keyboard),
        SwitchTo(Const('Назад'), id='back_get_mail', state=adminSG.get_mail),
        state=adminSG.get_time
    ),
    Window(
        Const('Введите кнопки которые будут крепиться к рассылаемому сообщению\n'
              'Введите кнопки в формате:\n кнопка1 - ссылка1\nкнопка2 - ссылка2'),
        TextInput(
            id='get_mail_keyboard',
            on_success=getters.get_mail_keyboard
        ),
        SwitchTo(Const('Продолжить без кнопок'), id='confirm_mail_switcher', state=adminSG.confirm_mail),
        SwitchTo(Const('Назад'), id='back_get_time', state=adminSG.get_time),
        state=adminSG.get_keyboard
    ),
    Window(
        Const('Вы подтверждаете рассылку сообщения'),
        Row(
            Button(Const('Да'), id='start_malling', on_click=getters.start_malling),
            Button(Const('Нет'), id='cancel_malling', on_click=getters.cancel_malling),
        ),
        SwitchTo(Const('Назад'), id='back_get_keyboard', state=adminSG.get_keyboard),
        state=adminSG.confirm_mail
    ),
)