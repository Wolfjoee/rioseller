"""Utility Functions"""
import re
from datetime import datetime
from typing import List, Optional
from aiogram.types import CallbackQuery
from config import Config, Emoji

def is_admin(user_id: int) -> bool:
    return user_id in Config.ADMIN_IDS

def format_price(amount: float) -> str:
    return f"{Config.CURRENCY}{amount:.2f}"

def format_datetime(dt_string: str) -> str:
    try:
        dt = datetime.strptime(dt_string, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d %b %Y, %I:%M %p")
    except:
        return dt_string

def validate_transaction_id(transaction_id: str) -> bool:
    if not transaction_id:
        return False
    cleaned = re.sub(r'[^A-Z0-9]', '', transaction_id.upper())
    return 10 <= len(cleaned) <= 20 and cleaned.isalnum()

def split_codes(text: str) -> List[str]:
    codes = re.split(r'[\n,\s]+', text.strip())
    codes = [code.strip() for code in codes if code.strip()]
    seen = set()
    unique_codes = []
    for code in codes:
        if code not in seen:
            seen.add(code)
            unique_codes.append(code)
    return unique_codes

async def safe_answer_callback(callback: CallbackQuery, text: Optional[str] = None):
    try:
        await callback.answer(text)
    except:
        pass

def format_coupon_detail(coupon: dict) -> str:
    text = f"{Emoji.COUPON} <b>{coupon['name']}</b>\n\n"
    if coupon.get('description'):
        text += f"{coupon['description']}\n\n"
    text += f"<b>{Emoji.MONEY} Price:</b> {format_price(coupon['price'])}\n"
    if coupon.get('original_price') and coupon['original_price'] > coupon['price']:
        discount = int(((coupon['original_price'] - coupon['price']) / coupon['original_price']) * 100)
        text += f"<b>{Emoji.SALE} Discount:</b> {discount}% OFF\n"
    text += f"\n"
    if coupon['available_stock'] > 0:
        text += f"<b>📦 Stock:</b> {coupon['available_stock']} available\n"
        if coupon['available_stock'] < 10:
            text += f"⚠️ <i>Limited stock!</i>\n"
    else:
        text += f"<b>❌ Out of Stock</b>\n"
    return text

def format_admin_order_detail(order: dict) -> str:
    text = f"{Emoji.ORDERS} <b>Order #{order['id']}</b>\n\n"
    text += f"<b>Coupon:</b> {order.get('coupon_name', 'N/A')}\n"
    text += f"<b>Quantity:</b> {order['quantity']}\n"
    text += f"<b>Total:</b> {format_price(order['total_price'])}\n\n"
    text += f"<b>Customer:</b>\n"
    text += f"User ID: <code>{order['user_id']}</code>\n"
    if order.get('username'):
        text += f"Username: @{order['username']}\n"
    text += f"\n<b>Payment:</b>\n"
    text += f"Transaction ID: <code>{order.get('transaction_id', 'N/A')}</code>\n"
    text += f"Screenshot: {'✅' if order.get('screenshot_file_id') else '❌'}\n\n"
    text += f"<b>Status:</b> {order['status'].title()}\n"
    text += f"<b>Created:</b> {format_datetime(order['created_at'])}\n"
    return text