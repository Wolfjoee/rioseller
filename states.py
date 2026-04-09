"""FSM States"""
from aiogram.fsm.state import State, StatesGroup

class CategoryStates(StatesGroup):
    entering_name = State()
    entering_description = State()

class CouponStates(StatesGroup):
    selecting_category = State()
    entering_name = State()
    entering_price = State()
    entering_description = State()
    uploading_codes = State()

class OrderStates(StatesGroup):
    entering_transaction_id = State()
    uploading_screenshot = State()
    entering_reject_reason = State()

class QRStates(StatesGroup):
    uploading_qr = State()
    entering_upi = State()

class BroadcastStates(StatesGroup):
    entering_message = State()
    confirming = State()