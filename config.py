"""Configuration"""
import os
from typing import List

class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_IDS: List[int] = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip().isdigit()]
    DB_FILE: str = os.getenv("DB_FILE", "coupon_bot.db")
    DEFAULT_UPI_ID: str = os.getenv("UPI_ID", "merchant@upi")
    CURRENCY: str = "₹"
    ITEMS_PER_PAGE: int = 8
    MAX_COUPON_PURCHASE: int = 10
    
    @classmethod
    def validate(cls) -> bool:
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is required!")
        if not cls.ADMIN_IDS:
            raise ValueError("ADMIN_IDS is required!")
        return True

class Emoji:
    CART = "🛒"
    MONEY = "💰"
    CHECK = "✅"
    CROSS = "❌"
    BACK = "⬅️"
    HOME = "🏠"
    CATEGORY = "📁"
    COUPON = "🎫"
    ADMIN = "👨‍💼"
    USER = "👤"
    ORDERS = "📦"
    PENDING = "⏳"
    APPROVED = "✅"
    REJECTED = "🚫"
    SETTINGS = "⚙️"
    BROADCAST = "📢"
    STATS = "📊"
    ADD = "➕"
    EDIT = "✏️"
    DELETE = "🗑️"
    UPLOAD = "📤"
    QR = "📱"
    HELP = "ℹ️"
    FIRE = "🔥"
    NEW = "🆕"
    SALE = "🏷️"

class Messages:
    WELCOME = """
{emoji} <b>Welcome to Coupon Store!</b>

Browse premium coupons at the best prices.
Choose a category below to get started!

💡 <i>Tip: Use /help for commands</i>
"""
    
    HELP_USER = """
<b>📚 User Commands</b>

/start - Start the bot
/browse - Browse coupons
/myorders - View orders
/help - Show help

<b>How to Purchase:</b>
1️⃣ Browse categories
2️⃣ Select coupon
3️⃣ Choose quantity
4️⃣ Pay via QR code
5️⃣ Submit transaction ID
6️⃣ Upload screenshot
7️⃣ Wait for approval
8️⃣ Receive coupons!
"""
    
    HELP_ADMIN = """
<b>👨‍💼 Admin Commands</b>

/admin - Admin panel
/pending - Pending orders

<b>Features:</b>
• Manage categories
• Add/edit coupons
• Upload coupon codes
• Approve/reject orders
• Update QR code
• Broadcast messages
• View statistics
"""
    
    ORDER_CREATED = """
<b>🎉 Order Created!</b>

Order ID: <code>#{order_id}</code>
Coupon: {coupon_name}
Quantity: {quantity}
Total: {currency}{total}

Status: ⏳ Pending Approval

You'll be notified once approved!
"""
    
    ORDER_APPROVED = """
<b>✅ Order Approved!</b>

Order ID: <code>#{order_id}</code>
Coupon: {coupon_name}

<b>Your Codes:</b>
{codes}

Thank you! 🎉
"""
    
    ORDER_REJECTED = """
<b>❌ Order Rejected</b>

Order ID: <code>#{order_id}</code>
Reason: {reason}

Contact admin for assistance.
"""