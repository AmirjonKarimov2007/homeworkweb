from aiogram.fsm.state import State, StatesGroup


class HomeworkStates(StatesGroup):
    choosing = State()
    submitting = State()
