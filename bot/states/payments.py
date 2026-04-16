from aiogram.fsm.state import State, StatesGroup


class PaymentStates(StatesGroup):
    choosing = State()
    uploading = State()
