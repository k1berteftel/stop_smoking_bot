from aiogram_dialog import DialogManager
from aiogram_dialog.context.intent_middleware import Context
from aiogram.fsm.context import FSMContext
from aiogram.filters import Filter
from aiogram.types import Message

from states import state_groups as states


class MsgStateFilter(Filter):
    async def __call__(self, msg: Message, **kwargs):
        dialog_context: Context = kwargs.get('aiogd_context')
        if dialog_context:
            allow_states = [states.startSG.get_voucher, states.startSG.get_derive_amount, states.startSG.get_derive_card]
            allow_states.extend(states.adminSG.__all_states__)
            print(dialog_context.state not in allow_states)
            return (bool(msg.text) and dialog_context.state not in allow_states)
        else:
            return bool(msg.text)