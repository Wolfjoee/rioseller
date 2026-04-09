"""Bot Handlers - ALL FIXED"""
import asyncio
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config import Config, Emoji, Messages
from database import db
from keyboards import Keyboards
from states import CategoryStates, CouponStates, OrderStates, QRStates, BroadcastStates
from utils import is_admin, format_price, format_datetime, validate_transaction_id, split_codes, safe_answer_callback, format_coupon_detail, format_admin_order_detail

logger = logging.getLogger(__name__)
router = Router()

# ==================== START & HELP ====================

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    db.add_user(message.from_user.id, message.from_user.username, message.from_user.first_name, message.from_user.last_name)
    await message.answer(Messages.WELCOME.format(emoji=Emoji.FIRE), reply_markup=Keyboards.main_menu(is_admin=is_admin(message.from_user.id)))

@router.message(Command("help"))
async def cmd_help(message: Message):
    if is_admin(message.from_user.id):
        await message.answer(Messages.HELP_ADMIN)
    await message.answer(Messages.HELP_USER)

@router.callback_query(F.data == "help")
async def callback_help(callback: CallbackQuery):
    await safe_answer_callback(callback)
    if is_admin(callback.from_user.id):
        await callback.message.answer(Messages.HELP_ADMIN)
    await callback.message.answer(Messages.HELP_USER)

@router.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await safe_answer_callback(callback)
    await callback.message.edit_text(Messages.WELCOME.format(emoji=Emoji.FIRE), reply_markup=Keyboards.main_menu(is_admin=is_admin(callback.from_user.id)))

# ==================== BROWSE (USER) ====================

@router.message(Command("browse"))
async def cmd_browse(message: Message):
    categories = db.get_categories(active_only=True)
    if not categories:
        await message.answer(f"{Emoji.CROSS} No categories available.", reply_markup=Keyboards.back_button("main_menu", "Main Menu"))
        return
    await message.answer(f"{Emoji.CATEGORY} <b>Browse Categories</b>\n\nSelect a category:", reply_markup=Keyboards.categories_menu(categories))

@router.callback_query(F.data == "browse_categories")
async def callback_browse_categories(callback: CallbackQuery):
    await safe_answer_callback(callback)
    categories = db.get_categories(active_only=True)
    if not categories:
        await callback.message.edit_text(f"{Emoji.CROSS} No categories available.", reply_markup=Keyboards.back_button("main_menu", "Main Menu"))
        return
    await callback.message.edit_text(f"{Emoji.CATEGORY} <b>Browse Categories</b>\n\nSelect a category:", reply_markup=Keyboards.categories_menu(categories))

@router.callback_query(F.data.startswith("category_"))
async def callback_view_category(callback: CallbackQuery):
    await safe_answer_callback(callback)
    category_id = int(callback.data.split("_")[1])
    category = db.get_category(category_id)
    if not category:
        await callback.answer("Category not found!", show_alert=True)
        return
    coupons = db.get_coupons(category_id=category_id, active_only=True)
    if not coupons:
        await callback.message.edit_text(f"{Emoji.CROSS} No coupons in this category.", reply_markup=Keyboards.back_button("browse_categories", "Back"))
        return
    text = f"{category.get('icon', Emoji.CATEGORY)} <b>{category['name']}</b>\n\n"
    if category.get('description'):
        text += f"{category['description']}\n\n"
    text += f"<b>Coupons:</b> {len(coupons)}"
    await callback.message.edit_text(text, reply_markup=Keyboards.coupons_menu(coupons, category_id))

# ==================== COUPON DETAIL & PURCHASE ====================

@router.callback_query(F.data.startswith("coupon_"))
async def callback_view_coupon(callback: CallbackQuery):
    await safe_answer_callback(callback)
    coupon_id = int(callback.data.split("_")[1])
    coupon = db.get_coupon(coupon_id)
    if not coupon:
        await callback.answer("Coupon not found!", show_alert=True)
        return
    await callback.message.edit_text(format_coupon_detail(coupon), reply_markup=Keyboards.coupon_detail(coupon, callback.from_user.id))

@router.callback_query(F.data.startswith("purchase_"))
async def callback_start_purchase(callback: CallbackQuery, state: FSMContext):
    await safe_answer_callback(callback)
    coupon_id = int(callback.data.split("_")[1])
    coupon = db.get_coupon(coupon_id)
    if not coupon or coupon['available_stock'] <= 0:
        await callback.answer("Out of stock!", show_alert=True)
        return
    text = f"{Emoji.CART} <b>Purchase {coupon['name']}</b>\n\n"
    text += f"Price: {format_price(coupon['price'])}\n"
    text += f"Available: {coupon['available_stock']}\n\n"
    text += f"Select quantity:"
    max_qty = min(coupon['max_purchase'], coupon['available_stock'])
    await callback.message.edit_text(text, reply_markup=Keyboards.quantity_selector(coupon_id, max_qty))
    await state.update_data(coupon_id=coupon_id)

@router.callback_query(F.data.startswith("qty_"))
async def callback_select_quantity(callback: CallbackQuery, state: FSMContext):
    await safe_answer_callback(callback)
    parts = callback.data.split("_")
    coupon_id = int(parts[1])
    quantity = int(parts[2])
    coupon = db.get_coupon(coupon_id)
    if not coupon or quantity > coupon['available_stock']:
        await callback.answer("Not available!", show_alert=True)
        return
    total_price = coupon['price'] * quantity
    qr_settings = db.get_qr_settings()
    text = f"{Emoji.MONEY} <b>Payment Details</b>\n\n"
    text += f"Coupon: {coupon['name']}\n"
    text += f"Quantity: {quantity}\n"
    text += f"Total: {format_price(total_price)}\n\n"
    text += f"<b>Instructions:</b>\n"
    text += f"1. Scan QR code below\n"
    text += f"2. Pay {format_price(total_price)}\n"
    if qr_settings and qr_settings.get('upi_id'):
        text += f"   to <code>{qr_settings['upi_id']}</code>\n"
    text += f"3. Take screenshot\n"
    text += f"4. Click 'I've Paid' below"
    await state.update_data(coupon_id=coupon_id, quantity=quantity, unit_price=coupon['price'], total_price=total_price)
    if qr_settings and qr_settings.get('file_id'):
        try:
            await callback.message.delete()
            await callback.message.answer_photo(photo=qr_settings['file_id'], caption=text, reply_markup=Keyboards.payment_confirmation())
        except:
            await callback.message.edit_text(text + f"\n\n⚠️ QR code error. Contact admin.", reply_markup=Keyboards.payment_confirmation())
    else:
        await callback.message.edit_text(text + f"\n\n⚠️ QR not set. Contact admin.", reply_markup=Keyboards.back_button("browse_categories", "Back"))

@router.callback_query(F.data == "submit_payment")
async def callback_submit_payment(callback: CallbackQuery, state: FSMContext):
    await safe_answer_callback(callback)
    text = f"{Emoji.UPLOAD} <b>Submit Payment Proof</b>\n\n"
    text += f"Send your <b>Transaction ID</b>\n\n"
    text += f"Example: <code>123456789012</code>"
    await callback.message.edit_text(text, reply_markup=Keyboards.cancel_order())
    await state.set_state(OrderStates.entering_transaction_id)

@router.message(OrderStates.entering_transaction_id)
async def process_transaction_id(message: Message, state: FSMContext):
    transaction_id = message.text.strip().upper()
    if not validate_transaction_id(transaction_id):
        await message.answer(f"{Emoji.CROSS} Invalid format! Try again:", reply_markup=Keyboards.cancel_order())
        return
    existing_orders = db.get_orders()
    if any(order.get('transaction_id') == transaction_id for order in existing_orders):
        await message.answer(f"{Emoji.CROSS} Already used! Send different ID:", reply_markup=Keyboards.cancel_order())
        return
    await state.update_data(transaction_id=transaction_id)
    text = f"{Emoji.CHECK} Transaction ID saved!\n\nNow upload payment screenshot:"
    await message.answer(text, reply_markup=Keyboards.cancel_order())
    await state.set_state(OrderStates.uploading_screenshot)

@router.message(OrderStates.uploading_screenshot, F.photo)
async def process_payment_screenshot(message: Message, state: FSMContext):
    data = await state.get_data()
    screenshot_file_id = message.photo[-1].file_id
    order_id = db.create_order(message.from_user.id, data['coupon_id'], data['quantity'], data['total_price'], data['transaction_id'], screenshot_file_id)
    if not order_id:
        await message.answer(f"{Emoji.CROSS} Failed. Try again.")
        await state.clear()
        return
    coupon = db.get_coupon(data['coupon_id'])
    await message.answer(Messages.ORDER_CREATED.format(order_id=order_id, coupon_name=coupon['name'], quantity=data['quantity'], currency=Config.CURRENCY, total=data['total_price']), reply_markup=Keyboards.back_button("main_menu", "Main Menu"))
    admin_text = f"{Emoji.NEW} <b>New Order!</b>\n\nOrder #{order_id}\nUser: {message.from_user.first_name}\nCoupon: {coupon['name']}\nQty: {data['quantity']}\nTotal: {format_price(data['total_price'])}\nTxn: <code>{data['transaction_id']}</code>"
    from bot import bot
    for admin_id in Config.ADMIN_IDS:
        try:
            await bot.send_photo(admin_id, screenshot_file_id, caption=admin_text, reply_markup=Keyboards.order_verification(order_id))
        except Exception as e:
            logger.error(f"Notify admin failed: {e}")
    await state.clear()

@router.message(OrderStates.uploading_screenshot)
async def handle_invalid_screenshot(message: Message):
    await message.answer(f"{Emoji.CROSS} Send a photo!", reply_markup=Keyboards.cancel_order())

@router.callback_query(F.data == "cancel_order")
async def callback_cancel_order(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await safe_answer_callback(callback, "Cancelled")
    await callback.message.edit_text(f"{Emoji.CROSS} Order cancelled", reply_markup=Keyboards.back_button("browse_categories", "Browse"))

# ==================== MY ORDERS ====================

@router.message(Command("myorders"))
async def cmd_my_orders(message: Message):
    orders = db.get_user_orders(message.from_user.id)
    if not orders:
        await message.answer(f"{Emoji.CROSS} No orders yet.", reply_markup=Keyboards.back_button("browse_categories", "Browse"))
        return
    text = f"{Emoji.ORDERS} <b>My Orders</b>\n\nTotal: {len(orders)}\nPending: {sum(1 for o in orders if o['status']=='pending')}"
    await message.answer(text, reply_markup=Keyboards.user_orders(orders))

@router.callback_query(F.data == "my_orders")
async def callback_my_orders(callback: CallbackQuery):
    await safe_answer_callback(callback)
    orders = db.get_user_orders(callback.from_user.id)
    if not orders:
        await callback.message.edit_text(f"{Emoji.CROSS} No orders yet.", reply_markup=Keyboards.back_button("main_menu", "Main Menu"))
        return
    text = f"{Emoji.ORDERS} <b>My Orders</b>\n\nTotal: {len(orders)}"
    await callback.message.edit_text(text, reply_markup=Keyboards.user_orders(orders))

@router.callback_query(F.data.startswith("user_order_"))
async def callback_view_user_order(callback: CallbackQuery):
    await safe_answer_callback(callback)
    order_id = int(callback.data.split("_")[2])
    order = db.get_order(order_id)
    if not order or order['user_id'] != callback.from_user.id:
        await callback.answer("Not found!", show_alert=True)
        return
    text = f"{Emoji.ORDERS} <b>Order #{order_id}</b>\n\n"
    text += f"Coupon: {order.get('coupon_name', 'N/A')}\n"
    text += f"Quantity: {order['quantity']}\n"
    text += f"Total: {format_price(order['total_price'])}\n"
    text += f"Status: {order['status'].title()}\n"
    if order['status'] in ['delivered', 'approved']:
        codes = db.get_order_coupon_codes(order_id)
        if codes:
            text += f"\n<b>Codes:</b>\n"
            for i, c in enumerate(codes, 1):
                text += f"{i}. <code>{c['code']}</code>\n"
    await callback.message.edit_text(text, reply_markup=Keyboards.back_button("my_orders", "Back"))

# ==================== ADMIN PANEL ====================

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer(f"{Emoji.CROSS} Access denied!")
        return
    stats = db.get_statistics()
    text = f"{Emoji.ADMIN} <b>Admin Panel</b>\n\n"
    text += f"Users: {stats.get('total_users', 0)}\n"
    text += f"Categories: {stats.get('total_categories', 0)}\n"
    text += f"Coupons: {stats.get('total_coupons', 0)}\n"
    text += f"Orders: {stats.get('total_orders', 0)}\n"
    text += f"Pending: {stats.get('pending_orders', 0)}\n"
    text += f"Revenue: {format_price(stats.get('total_revenue', 0))}"
    await message.answer(text, reply_markup=Keyboards.admin_panel())

@router.callback_query(F.data == "admin_panel")
async def callback_admin_panel(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied!", show_alert=True)
        return
    await state.clear()
    await safe_answer_callback(callback)
    stats = db.get_statistics()
    text = f"{Emoji.ADMIN} <b>Admin Panel</b>\n\n"
    text += f"Users: {stats.get('total_users', 0)}\n"
    text += f"Categories: {stats.get('total_categories', 0)}\n"
    text += f"Coupons: {stats.get('total_coupons', 0)}\n"
    text += f"Pending: {stats.get('pending_orders', 0)}"
    await callback.message.edit_text(text, reply_markup=Keyboards.admin_panel())
    # ==================== ADMIN - CATEGORIES ====================

@router.callback_query(F.data == "admin_categories")
async def callback_admin_categories(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied!", show_alert=True)
        return
    await safe_answer_callback(callback)
    categories = db.get_categories(active_only=False)
    text = f"{Emoji.CATEGORY} <b>Manage Categories</b>\n\nTotal: {len(categories)}"
    await callback.message.edit_text(text, reply_markup=Keyboards.admin_categories(categories))

@router.callback_query(F.data == "admin_add_category")
async def callback_admin_add_category(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied!", show_alert=True)
        return
    await safe_answer_callback(callback)
    text = f"{Emoji.ADD} <b>Add Category</b>\n\nEnter category name:"
    await callback.message.edit_text(text, reply_markup=Keyboards.cancel_button())
    await state.set_state(CategoryStates.entering_name)

@router.message(CategoryStates.entering_name)
async def process_category_name(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    name = message.text.strip()
    if len(name) < 2 or len(name) > 100:
        await message.answer(f"{Emoji.CROSS} Name must be 2-100 characters!", reply_markup=Keyboards.cancel_button())
        return
    await state.update_data(category_name=name)
    text = f"{Emoji.EDIT} <b>Add Description</b>\n\nCategory: {name}\n\nEnter description or /skip:"
    await message.answer(text, reply_markup=Keyboards.cancel_button())
    await state.set_state(CategoryStates.entering_description)

@router.message(CategoryStates.entering_description)
async def process_category_description(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    description = None if message.text == "/skip" else message.text.strip()
    category_id = db.add_category(data['category_name'], description)
    if category_id:
        text = f"{Emoji.CHECK} <b>Category Created!</b>\n\nName: {data['category_name']}\nID: {category_id}"
        await message.answer(text, reply_markup=Keyboards.back_button("admin_categories", "Categories"))
    else:
        await message.answer(f"{Emoji.CROSS} Failed! Name may exist.", reply_markup=Keyboards.back_button("admin_categories", "Categories"))
    await state.clear()

@router.callback_query(F.data.startswith("admin_cat_"))
async def callback_admin_category_detail(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied!", show_alert=True)
        return
    await safe_answer_callback(callback)
    category_id = int(callback.data.split("_")[2])
    category = db.get_category(category_id)
    if not category:
        await callback.answer("Not found!", show_alert=True)
        return
    coupons = db.get_coupons(category_id=category_id, active_only=False)
    text = f"{Emoji.CATEGORY} <b>Category Details</b>\n\n"
    text += f"Name: {category['name']}\n"
    text += f"Description: {category.get('description', 'None')}\n"
    text += f"Coupons: {len(coupons)}\n"
    text += f"Status: {'✅ Active' if category['is_active'] else '❌ Inactive'}"
    await callback.message.edit_text(text, reply_markup=Keyboards.admin_category_detail(category_id, category['is_active']))

@router.callback_query(F.data.startswith("admin_toggle_cat_"))
async def callback_admin_toggle_category(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied!", show_alert=True)
        return
    category_id = int(callback.data.split("_")[3])
    category = db.get_category(category_id)
    if not category:
        await callback.answer("Not found!", show_alert=True)
        return
    new_status = 0 if category['is_active'] else 1
    if db.update_category(category_id, is_active=new_status):
        await callback.answer(f"{'Activated' if new_status else 'Deactivated'}!", show_alert=True)
        category = db.get_category(category_id)
        coupons = db.get_coupons(category_id=category_id, active_only=False)
        text = f"{Emoji.CATEGORY} <b>Category Details</b>\n\n"
        text += f"Name: {category['name']}\n"
        text += f"Coupons: {len(coupons)}\n"
        text += f"Status: {'✅ Active' if category['is_active'] else '❌ Inactive'}"
        await callback.message.edit_text(text, reply_markup=Keyboards.admin_category_detail(category_id, category['is_active']))
    else:
        await callback.answer("Failed!", show_alert=True)

@router.callback_query(F.data.startswith("admin_delete_cat_"))
async def callback_admin_delete_category(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied!", show_alert=True)
        return
    await safe_answer_callback(callback)
    category_id = int(callback.data.split("_")[3])
    coupons = db.get_coupons(category_id=category_id, active_only=False)
    if coupons:
        await callback.answer(f"Cannot delete! Has {len(coupons)} coupon(s)", show_alert=True)
        return
    if db.delete_category(category_id):
        await callback.answer("Deleted!", show_alert=True)
        categories = db.get_categories(active_only=False)
        text = f"{Emoji.CATEGORY} <b>Manage Categories</b>\n\nTotal: {len(categories)}"
        await callback.message.edit_text(text, reply_markup=Keyboards.admin_categories(categories))
    else:
        await callback.answer("Failed!", show_alert=True)

# ==================== ADMIN - COUPONS ====================

@router.callback_query(F.data == "admin_coupons")
async def callback_admin_coupons(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied!", show_alert=True)
        return
    await safe_answer_callback(callback)
    coupons = db.get_coupons(active_only=False)
    text = f"{Emoji.COUPON} <b>Manage Coupons</b>\n\nTotal: {len(coupons)}"
    await callback.message.edit_text(text, reply_markup=Keyboards.admin_coupons(coupons))

@router.callback_query(F.data == "admin_add_coupon")
async def callback_admin_add_coupon(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied!", show_alert=True)
        return
    await safe_answer_callback(callback)
    categories = db.get_categories(active_only=True)
    if not categories:
        await callback.answer("Create a category first!", show_alert=True)
        await callback.message.edit_text(f"{Emoji.CROSS} No categories! Create one first.", reply_markup=Keyboards.back_button("admin_categories", "Categories"))
        return
    text = f"{Emoji.ADD} <b>Add Coupon</b>\n\nStep 1: Select category"
    await callback.message.edit_text(text, reply_markup=Keyboards.select_category_for_coupon(categories))
    await state.set_state(CouponStates.selecting_category)

@router.callback_query(CouponStates.selecting_category, F.data.startswith("select_cat_"))
async def callback_select_coupon_category(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied!", show_alert=True)
        return
    await safe_answer_callback(callback)
    category_id = int(callback.data.split("_")[2])
    category = db.get_category(category_id)
    if not category:
        await callback.answer("Not found!", show_alert=True)
        await state.clear()
        return
    await state.update_data(category_id=category_id, category_name=category['name'])
    text = f"{Emoji.EDIT} <b>Add Coupon</b>\n\nCategory: {category['name']}\n\nStep 2: Enter coupon name"
    await callback.message.edit_text(text, reply_markup=Keyboards.cancel_button())
    await state.set_state(CouponStates.entering_name)

@router.message(CouponStates.entering_name)
async def process_coupon_name(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    name = message.text.strip()
    if len(name) < 3 or len(name) > 200:
        await message.answer(f"{Emoji.CROSS} Name must be 3-200 characters!", reply_markup=Keyboards.cancel_button())
        return
    data = await state.get_data()
    await state.update_data(coupon_name=name)
    text = f"{Emoji.MONEY} <b>Add Coupon</b>\n\nCategory: {data['category_name']}\nName: {name}\n\nStep 3: Enter price (number only)\n\nExample: 99 or 99.50"
    await message.answer(text, reply_markup=Keyboards.cancel_button())
    await state.set_state(CouponStates.entering_price)

@router.message(CouponStates.entering_price)
async def process_coupon_price(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        price = float(message.text.strip())
        if price <= 0:
            raise ValueError
    except:
        await message.answer(f"{Emoji.CROSS} Invalid price!\n\nEnter a number: 99 or 99.50", reply_markup=Keyboards.cancel_button())
        return
    data = await state.get_data()
    await state.update_data(price=price)
    text = f"{Emoji.EDIT} <b>Add Coupon</b>\n\nCategory: {data['category_name']}\nName: {data['coupon_name']}\nPrice: {format_price(price)}\n\nStep 4: Enter description or /skip"
    await message.answer(text, reply_markup=Keyboards.cancel_button())
    await state.set_state(CouponStates.entering_description)

@router.message(CouponStates.entering_description)
async def process_coupon_description(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    description = None if message.text.strip() == "/skip" else message.text.strip()
    try:
        coupon_id = db.add_coupon(data['category_id'], data['coupon_name'], data['price'], description)
        if coupon_id:
            text = f"{Emoji.CHECK} <b>Coupon Created!</b>\n\n"
            text += f"Name: {data['coupon_name']}\n"
            text += f"Category: {data['category_name']}\n"
            text += f"Price: {format_price(data['price'])}\n"
            text += f"ID: {coupon_id}\n\n"
            text += f"⚠️ Stock is 0. Upload codes to activate!"
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=f"{Emoji.UPLOAD} Upload Codes", callback_data=f"admin_upload_codes_{coupon_id}")],
                [InlineKeyboardButton(text=f"{Emoji.BACK} Back", callback_data="admin_coupons")]
            ])
            await message.answer(text, reply_markup=keyboard)
        else:
            await message.answer(f"{Emoji.CROSS} Failed! Name may exist in category.", reply_markup=Keyboards.back_button("admin_coupons", "Coupons"))
    except Exception as e:
        logger.error(f"Create coupon error: {e}")
        await message.answer(f"{Emoji.CROSS} Error: {str(e)}", reply_markup=Keyboards.back_button("admin_coupons", "Coupons"))
    await state.clear()

@router.callback_query(F.data.startswith("admin_cpn_"))
async def callback_admin_coupon_detail(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied!", show_alert=True)
        return
    await safe_answer_callback(callback)
    coupon_id = int(callback.data.split("_")[2])
    coupon = db.get_coupon(coupon_id)
    if not coupon:
        await callback.answer("Not found!", show_alert=True)
        return
    text = f"{Emoji.COUPON} <b>Coupon Details</b>\n\n"
    text += f"Name: {coupon['name']}\n"
    text += f"Category: {coupon.get('category_name', 'N/A')}\n"
    text += f"Price: {format_price(coupon['price'])}\n"
    text += f"Stock: {coupon['stock']}\n"
    text += f"Available: {coupon['available_stock']}\n"
    text += f"Sold: {coupon['sold_count']}\n"
    text += f"Status: {'✅ Active' if coupon['is_active'] else '❌ Inactive'}"
    await callback.message.edit_text(text, reply_markup=Keyboards.admin_coupon_detail(coupon_id, coupon['is_active']))

@router.callback_query(F.data.startswith("admin_upload_codes_"))
async def callback_admin_upload_codes(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied!", show_alert=True)
        return
    await safe_answer_callback(callback)
    coupon_id = int(callback.data.split("_")[3])
    coupon = db.get_coupon(coupon_id)
    if not coupon:
        await callback.answer("Not found!", show_alert=True)
        return
    text = f"{Emoji.UPLOAD} <b>Upload Codes</b>\n\n"
    text += f"Coupon: {coupon['name']}\n"
    text += f"Current Stock: {coupon['available_stock']}\n\n"
    text += f"Send codes (one per line or comma-separated):\n\n"
    text += f"<code>CODE1\nCODE2\nCODE3</code>\n\nor\n<code>CODE1, CODE2, CODE3</code>"
    await callback.message.edit_text(text, reply_markup=Keyboards.cancel_button())
    await state.update_data(coupon_id=coupon_id)
    await state.set_state(CouponStates.uploading_codes)

@router.message(CouponStates.uploading_codes)
async def process_coupon_codes(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    coupon_id = data['coupon_id']
    codes = split_codes(message.text)
    if not codes:
        await message.answer(f"{Emoji.CROSS} No valid codes found!", reply_markup=Keyboards.cancel_button())
        return
    added, duplicates = db.add_coupon_codes(coupon_id, codes)
    coupon = db.get_coupon(coupon_id)
    text = f"{Emoji.CHECK} <b>Upload Complete!</b>\n\n"
    text += f"✅ Added: {added}\n"
    if duplicates > 0:
        text += f"⚠️ Duplicates: {duplicates}\n"
    text += f"\nTotal Available: {coupon['available_stock']}"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{Emoji.CHECK} Done", callback_data=f"admin_cpn_{coupon_id}")],
        [InlineKeyboardButton(text=f"{Emoji.CROSS} Cancel", callback_data="admin_coupons")]
    ])
    await message.answer(text, reply_markup=keyboard)

@router.callback_query(F.data.startswith("admin_toggle_cpn_"))
async def callback_admin_toggle_coupon(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied!", show_alert=True)
        return
    coupon_id = int(callback.data.split("_")[3])
    coupon = db.get_coupon(coupon_id)
    if not coupon:
        await callback.answer("Not found!", show_alert=True)
        return
    new_status = 0 if coupon['is_active'] else 1
    if db.update_coupon(coupon_id, is_active=new_status):
        await callback.answer(f"{'Activated' if new_status else 'Deactivated'}!", show_alert=True)
        coupon = db.get_coupon(coupon_id)
        text = f"{Emoji.COUPON} <b>Coupon Details</b>\n\n"
        text += f"Name: {coupon['name']}\n"
        text += f"Price: {format_price(coupon['price'])}\n"
        text += f"Available: {coupon['available_stock']}\n"
        text += f"Status: {'✅ Active' if coupon['is_active'] else '❌ Inactive'}"
        await callback.message.edit_text(text, reply_markup=Keyboards.admin_coupon_detail(coupon_id, coupon['is_active']))
    else:
        await callback.answer("Failed!", show_alert=True)

@router.callback_query(F.data.startswith("admin_delete_cpn_"))
async def callback_admin_delete_coupon(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied!", show_alert=True)
        return
    await safe_answer_callback(callback)
    coupon_id = int(callback.data.split("_")[3])
    if db.delete_coupon(coupon_id):
        await callback.answer("Deleted!", show_alert=True)
        coupons = db.get_coupons(active_only=False)
        text = f"{Emoji.COUPON} <b>Manage Coupons</b>\n\nTotal: {len(coupons)}"
        await callback.message.edit_text(text, reply_markup=Keyboards.admin_coupons(coupons))
    else:
        await callback.answer("Failed!", show_alert=True)# ==================== ADMIN - ORDERS ====================

@router.callback_query(F.data == "admin_pending_orders")
async def callback_admin_pending_orders(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied!", show_alert=True)
        return
    await safe_answer_callback(callback)
    orders = db.get_orders(status='pending')
    if not orders:
        await callback.message.edit_text(f"{Emoji.CHECK} No pending orders!", reply_markup=Keyboards.back_button("admin_panel", "Admin"))
        return
    text = f"{Emoji.PENDING} <b>Pending Orders</b>\n\nTotal: {len(orders)}"
    await callback.message.edit_text(text, reply_markup=Keyboards.admin_orders(orders, "pending"))

@router.callback_query(F.data == "admin_all_orders")
async def callback_admin_all_orders(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied!", show_alert=True)
        return
    await safe_answer_callback(callback)
    orders = db.get_orders()
    if not orders:
        await callback.message.edit_text(f"{Emoji.CROSS} No orders!", reply_markup=Keyboards.back_button("admin_panel", "Admin"))
        return
    text = f"{Emoji.ORDERS} <b>All Orders</b>\n\nTotal: {len(orders)}"
    await callback.message.edit_text(text, reply_markup=Keyboards.admin_orders(orders, "all"))

@router.callback_query(F.data.startswith("admin_order_"))
async def callback_admin_order_detail(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied!", show_alert=True)
        return
    await safe_answer_callback(callback)
    order_id = int(callback.data.split("_")[2])
    order = db.get_order(order_id)
    if not order:
        await callback.answer("Not found!", show_alert=True)
        return
    text = format_admin_order_detail(order)
    keyboard = Keyboards.order_verification(order_id) if order['status'] == 'pending' else Keyboards.back_button("admin_all_orders", "Orders")
    await callback.message.edit_text(text, reply_markup=keyboard)

@router.callback_query(F.data.startswith("view_screenshot_"))
async def callback_view_screenshot(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied!", show_alert=True)
        return
    await safe_answer_callback(callback)
    order_id = int(callback.data.split("_")[2])
    order = db.get_order(order_id)
    if not order or not order.get('screenshot_file_id'):
        await callback.answer("No screenshot!", show_alert=True)
        return
    try:
        await callback.message.answer_photo(order['screenshot_file_id'], caption=f"Order #{order_id} Screenshot")
    except Exception as e:
        logger.error(f"Screenshot error: {e}")
        await callback.answer("Failed to load!", show_alert=True)

@router.callback_query(F.data.startswith("approve_order_"))
async def callback_approve_order(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied!", show_alert=True)
        return
    await safe_answer_callback(callback, "Processing...")
    order_id = int(callback.data.split("_")[2])
    order = db.get_order(order_id)
    if not order or order['status'] != 'pending':
        await callback.answer("Order already processed!", show_alert=True)
        return
    coupon = db.get_coupon(order['coupon_id'])
    if coupon['available_stock'] < order['quantity']:
        await callback.answer(f"Not enough stock! Available: {coupon['available_stock']}", show_alert=True)
        return
    success = db.approve_order(order_id, order['user_id'])
    if success:
        codes = db.get_order_coupon_codes(order_id)
        user_text = Messages.ORDER_APPROVED.format(
            order_id=order_id,
            coupon_name=coupon['name'],
            codes="\n".join([f"{i}. <code>{c['code']}</code>" for i, c in enumerate(codes, 1)])
        )
        from bot import bot
        try:
            await bot.send_message(order['user_id'], user_text)
        except Exception as e:
            logger.error(f"User notify failed: {e}")
        await callback.answer("✅ Approved & delivered!", show_alert=True)
        text = format_admin_order_detail(db.get_order(order_id))
        await callback.message.edit_text(text, reply_markup=Keyboards.back_button("admin_pending_orders", "Pending"))
    else:
        await callback.answer("Failed!", show_alert=True)

@router.callback_query(F.data.startswith("reject_order_"))
async def callback_reject_order(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied!", show_alert=True)
        return
    await safe_answer_callback(callback)
    order_id = int(callback.data.split("_")[2])
    order = db.get_order(order_id)
    if not order or order['status'] != 'pending':
        await callback.answer("Already processed!", show_alert=True)
        return
    text = f"{Emoji.REJECTED} <b>Reject Order #{order_id}</b>\n\nEnter rejection reason:"
    await callback.message.edit_text(text, reply_markup=Keyboards.cancel_button())
    await state.update_data(reject_order_id=order_id)
    await state.set_state(OrderStates.entering_reject_reason)

@router.message(OrderStates.entering_reject_reason)
async def process_reject_reason(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    order_id = data['reject_order_id']
    reason = message.text.strip()
    order = db.get_order(order_id)
    if not order:
        await message.answer("Order not found!")
        await state.clear()
        return
    success = db.reject_order(order_id, reason)
    if success:
        coupon = db.get_coupon(order['coupon_id'])
        user_text = Messages.ORDER_REJECTED.format(order_id=order_id, coupon_name=coupon['name'], reason=reason)
        from bot import bot
        try:
            await bot.send_message(order['user_id'], user_text)
        except Exception as e:
            logger.error(f"User notify failed: {e}")
        await message.answer(f"{Emoji.CHECK} Order rejected & user notified.", reply_markup=Keyboards.back_button("admin_pending_orders", "Pending"))
    else:
        await message.answer(f"{Emoji.CROSS} Failed!", reply_markup=Keyboards.back_button("admin_panel", "Admin"))
    await state.clear()

# ==================== ADMIN - QR CODE ====================

@router.callback_query(F.data == "admin_update_qr")
async def callback_admin_update_qr(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied!", show_alert=True)
        return
    await safe_answer_callback(callback)
    qr_settings = db.get_qr_settings()
    text = f"{Emoji.QR} <b>Update QR Code</b>\n\n"
    if qr_settings:
        text += f"Current UPI: <code>{qr_settings.get('upi_id', 'Not set')}</code>\n"
        text += f"QR: {'✅ Uploaded' if qr_settings.get('file_id') else '❌ Not set'}\n\n"
    text += f"Send new QR code image:"
    await callback.message.edit_text(text, reply_markup=Keyboards.cancel_button())
    await state.set_state(QRStates.uploading_qr)

@router.message(QRStates.uploading_qr, F.photo)
async def process_qr_upload(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    file_id = message.photo[-1].file_id
    text = f"{Emoji.CHECK} QR received!\n\nNow enter UPI ID or /skip:"
    await state.update_data(qr_file_id=file_id)
    await message.answer(text, reply_markup=Keyboards.cancel_button())
    await state.set_state(QRStates.entering_upi)

@router.message(QRStates.uploading_qr)
async def handle_invalid_qr(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(f"{Emoji.CROSS} Send a photo!", reply_markup=Keyboards.cancel_button())

@router.message(QRStates.entering_upi)
async def process_upi_id(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    upi_id = None if message.text == "/skip" else message.text.strip()
    if upi_id and '@' not in upi_id:
        await message.answer(f"{Emoji.CROSS} Invalid UPI format!\n\nExample: merchant@paytm\n\nOr /skip", reply_markup=Keyboards.cancel_button())
        return
    success = db.update_qr_settings(data['qr_file_id'], upi_id)
    if success:
        text = f"{Emoji.CHECK} <b>QR Updated!</b>\n\n"
        if upi_id:
            text += f"UPI: <code>{upi_id}</code>"
        await message.answer(text, reply_markup=Keyboards.back_button("admin_panel", "Admin"))
    else:
        await message.answer(f"{Emoji.CROSS} Failed!", reply_markup=Keyboards.back_button("admin_panel", "Admin"))
    await state.clear()

# ==================== ADMIN - BROADCAST ====================

@router.callback_query(F.data == "admin_broadcast")
async def callback_admin_broadcast(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied!", show_alert=True)
        return
    await safe_answer_callback(callback)
    users = db.get_all_users(active_only=True)
    text = f"{Emoji.BROADCAST} <b>Broadcast Message</b>\n\nActive users: {len(users)}\n\nEnter message (HTML supported):"
    await callback.message.edit_text(text, reply_markup=Keyboards.cancel_button())
    await state.set_state(BroadcastStates.entering_message)

@router.message(BroadcastStates.entering_message)
async def process_broadcast_message(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    broadcast_text = message.text or ""
    if not broadcast_text.strip():
        await message.answer(f"{Emoji.CROSS} Empty message!", reply_markup=Keyboards.cancel_button())
        return
    await state.update_data(broadcast_message=broadcast_text)
    users = db.get_all_users(active_only=True)
    preview = f"{Emoji.BROADCAST} <b>Preview</b>\n\nRecipients: {len(users)}\n\n{broadcast_text}\n\nConfirm?"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{Emoji.CHECK} Send", callback_data="confirm_broadcast")],
        [InlineKeyboardButton(text=f"{Emoji.CROSS} Cancel", callback_data="admin_panel")]
    ])
    await message.answer(preview, reply_markup=keyboard)
    await state.set_state(BroadcastStates.confirming)

@router.callback_query(BroadcastStates.confirming, F.data == "confirm_broadcast")
async def callback_confirm_broadcast(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied!", show_alert=True)
        return
    await safe_answer_callback(callback, "Sending...")
    data = await state.get_data()
    broadcast_message = data['broadcast_message']
    users = db.get_all_users(active_only=True)
    total = len(users)
    successful = 0
    failed = 0
    progress_msg = await callback.message.edit_text(f"{Emoji.BROADCAST} Broadcasting...\n\nProgress: 0/{total}")
    from bot import bot
    for i, user in enumerate(users, 1):
        try:
            await bot.send_message(user['user_id'], broadcast_message, disable_web_page_preview=True)
            successful += 1
        except Exception as e:
            logger.error(f"Broadcast to {user['user_id']} failed: {e}")
            failed += 1
        if i % 10 == 0 or i == total:
            try:
                await progress_msg.edit_text(f"{Emoji.BROADCAST} Broadcasting...\n\nProgress: {i}/{total}\n✅ Success: {successful}\n❌ Failed: {failed}")
            except:
                pass
        await asyncio.sleep(0.05)
    db.add_broadcast(callback.from_user.id, broadcast_message, total, successful, failed)
    final_text = f"{Emoji.CHECK} <b>Broadcast Complete!</b>\n\nTotal: {total}\n✅ Success: {successful}\n❌ Failed: {failed}"
    await progress_msg.edit_text(final_text, reply_markup=Keyboards.back_button("admin_panel", "Admin"))
    await state.clear()

# ==================== ADMIN - STATISTICS ====================

@router.callback_query(F.data == "admin_stats")
async def callback_admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied!", show_alert=True)
        return
    await safe_answer_callback(callback)
    stats = db.get_statistics()
    text = f"{Emoji.STATS} <b>Statistics</b>\n\n"
    text += f"<b>👥 Users</b>\n"
    text += f"Total: {stats.get('total_users', 0)}\n\n"
    text += f"<b>📁 Categories</b>\n"
    text += f"Total: {stats.get('total_categories', 0)}\n\n"
    text += f"<b>🎫 Coupons</b>\n"
    text += f"Total: {stats.get('total_coupons', 0)}\n\n"
    text += f"<b>📦 Orders</b>\n"
    text += f"Total: {stats.get('total_orders', 0)}\n"
    text += f"Pending: {stats.get('pending_orders', 0)}\n"
    text += f"Approved: {stats.get('approved_orders', 0)}\n\n"
    text += f"<b>💰 Revenue</b>\n"
    text += f"Total: {format_price(stats.get('total_revenue', 0))}\n"
    text += f"Today: {format_price(stats.get('today_revenue', 0))}"
    await callback.message.edit_text(text, reply_markup=Keyboards.back_button("admin_panel", "Admin"))

@router.callback_query(F.data == "admin_users")
async def callback_admin_users(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied!", show_alert=True)
        return
    await safe_answer_callback(callback)
    users = db.get_all_users(active_only=False)
    text = f"{Emoji.USER} <b>User Management</b>\n\n"
    text += f"Total: {len(users)}\n"
    text += f"Active: {sum(1 for u in users if not u['is_blocked'])}\n\n"
    recent = sorted(users, key=lambda x: x['joined_at'], reverse=True)[:5]
    text += f"<b>Recent Users:</b>\n"
    for user in recent:
        username = f"@{user['username']}" if user['username'] else "No username"
        text += f"• {user['first_name']} ({username})\n"
    await callback.message.edit_text(text, reply_markup=Keyboards.back_button("admin_panel", "Admin"))

# ==================== CANCEL ====================

@router.callback_query(F.data == "cancel")
async def callback_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await safe_answer_callback(callback, "Cancelled")
    keyboard = Keyboards.back_button("admin_panel", "Admin") if is_admin(callback.from_user.id) else Keyboards.back_button("main_menu", "Main Menu")
    await callback.message.edit_text(f"{Emoji.CROSS} Operation cancelled", reply_markup=keyboard)

# ==================== OUT OF STOCK ====================

@router.callback_query(F.data == "out_of_stock")
async def callback_out_of_stock(callback: CallbackQuery):
    await callback.answer("This item is out of stock!", show_alert=True)