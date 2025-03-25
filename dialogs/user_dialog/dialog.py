from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import SwitchTo, Column, Row, Button, Group, Select, Start, Url
from aiogram_dialog.widgets.text import Format, Const
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.media import DynamicMedia

from dialogs.user_dialog import getters

from states.state_groups import startSG, adminSG

user_dialog = Dialog(
    Window(
        Format('{text}'),
        Column(
            SwitchTo(Format('{sub}'), id='sub_menu_switcher', state=startSG.sub_menu),
            SwitchTo(Format('{ref}'), id='ref_menu_switcher', state=startSG.ref_menu),
            SwitchTo(Format('{info}'), id='info_switcher', state=startSG.info),
            Button(Format('{close}'), id='close_dialog', on_click=getters.close_dialog),
            Start(Const('Админ панель'), id='admin', state=adminSG.start, when='admin')
        ),
        getter=getters.start_getter,
        state=startSG.start
    ),
    Window(  # для тех у кого уже есть подписка другой текст и нету кнопок
        Format('{text}'),
        Column(
            Button(Format('{rub}'), id='rub_payment_choose', on_click=getters.choose_payment, when='ru'),
            Button(Format('{stars}'), id='stars_payment_choose', on_click=getters.choose_payment),
            #Button(Format('{ton}'), id='ton_payment_choose', on_click=getters.choose_payment)
        ),
        SwitchTo(Format('{back}'), id='back', state=startSG.start),
        getter=getters.sub_menu_getter,
        state=startSG.sub_menu
    ),
    Window(
        Format('{text}'),
        Column(
            Url(Format('{payment}'), id='payment_link', url=Format('{url}')),
        ),
        Button(Format('{back}'), id='back_sub_menu', on_click=getters.close_rub_payment),
        getter=getters.rub_payment_getter,
        state=startSG.rub_payment_menu
    ),
    Window(
        Format('{text}'),
        Column(
            Url(Format('{share}'), url=Format('http://t.me/share/url?url=https://t.me/AiStopSmoking_bot?start={user_id}')),
            SwitchTo(Format('{derive}'), id='derive_switcher', state=startSG.get_derive_amount),
        ),
        SwitchTo(Format('{back}'), id='back', state=startSG.start),
        getter=getters.ref_menu_getter,
        state=startSG.ref_menu
    ),
    Window(
        Format('{text}'),
        SwitchTo(Format('{back}'), id='back', state=startSG.start),
        getter=getters.info_getter,
        state=startSG.info
    ),
)