"""Inline Keyboard Builders"""
from typing import List, Dict
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config, Emoji

class Keyboards:
    
    @staticmethod
    def main_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
        buttons = [
            [InlineKeyboardButton(text=f"{Emoji.CATEGORY} Browse Categories", callback_data="browse_categories")],
            [InlineKeyboardButton(text=f"{Emoji.ORDERS} My Orders", callback_data="my_orders")],
            [InlineKeyboardButton(text=f"{Emoji.HELP} Help", callback_data="help")]
        ]
        if is_admin:
            buttons.append([InlineKeyboardButton(text=f"{Emoji.ADMIN} Admin Panel", callback_data="admin_panel")])
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def categories_menu(categories: List[Dict]) -> InlineKeyboardMarkup:
        buttons = []
        for cat in categories:
            buttons.append([InlineKeyboardButton(
                text=f"{cat.get('icon', Emoji.CATEGORY)} {cat['name']} ({cat.get('coupon_count', 0)})",
                callback_data=f"category_{cat['id']}"
            )])
        buttons.append([InlineKeyboardButton(text=f"{Emoji.HOME} Main Menu", callback_data="main_menu")])
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def coupons_menu(coupons: List[Dict], category_id: int) -> InlineKeyboardMarkup:
        buttons = []
        for coupon in coupons:
            stock_info = f"({coupon['available_stock']} left)" if coupon['available_stock'] < 50 else ""
            buttons.append([InlineKeyboardButton(
                text=f"{coupon['name']} - {Config.CURRENCY}{coupon['price']:.2f} {stock_info}",
                callback_data=f"coupon_{coupon['id']}"
            )])
        buttons.append([InlineKeyboardButton(text=f"{Emoji.BACK} Back", callback_data="browse_categories")])
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def coupon_detail(coupon: Dict, user_id: int = None) -> InlineKeyboardMarkup:
        buttons = []
        if coupon['available_stock'] > 0:
            buttons.append([InlineKeyboardButton(text=f"{Emoji.CART} Purchase Now", callback_data=f"purchase_{coupon['id']}")])
        else:
            buttons.append([InlineKeyboardButton(text=f"{Emoji.CROSS} Out of Stock", callback_data="out_of_stock")])
        buttons.append([InlineKeyboardButton(text=f"{Emoji.BACK} Back", callback_data=f"category_{coupon['category_id']}")])
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def quantity_selector(coupon_id: int, max_qty: int) -> InlineKeyboardMarkup:
        buttons = []
        qty_row = []
        for i in range(1, min(max_qty + 1, 11)):
            qty_row.append(InlineKeyboardButton(text=str(i), callback_data=f"qty_{coupon_id}_{i}"))
            if i % 5 == 0:
                buttons.append(qty_row)
                qty_row = []
        if qty_row:
            buttons.append(qty_row)
        buttons.append([InlineKeyboardButton(text=f"{Emoji.BACK} Back", callback_data=f"coupon_{coupon_id}")])
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def payment_confirmation() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"{Emoji.CHECK} I've Paid - Submit Proof", callback_data="submit_payment")],
            [InlineKeyboardButton(text=f"{Emoji.CROSS} Cancel Order", callback_data="cancel_order")]
        ])
    
    @staticmethod
    def cancel_order() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"{Emoji.CROSS} Cancel Order", callback_data="cancel_order")]
        ])
    
    @staticmethod
    def user_orders(orders: List[Dict]) -> InlineKeyboardMarkup:
        buttons = []
        status_emoji = {'pending': Emoji.PENDING, 'approved': Emoji.APPROVED, 'delivered': Emoji.APPROVED, 'rejected': Emoji.REJECTED}
        for order in orders[:10]:
            emoji = status_emoji.get(order['status'], '')
            buttons.append([InlineKeyboardButton(
                text=f"{emoji} Order #{order['id']} - {order.get('coupon_name', 'N/A')}",
                callback_data=f"user_order_{order['id']}"
            )])
        buttons.append([InlineKeyboardButton(text=f"{Emoji.HOME} Main Menu", callback_data="main_menu")])
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def admin_panel() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"{Emoji.CATEGORY} Manage Categories", callback_data="admin_categories")],
            [InlineKeyboardButton(text=f"{Emoji.COUPON} Manage Coupons", callback_data="admin_coupons")],
            [InlineKeyboardButton(text=f"{Emoji.PENDING} Pending Orders", callback_data="admin_pending_orders")],
            [InlineKeyboardButton(text=f"{Emoji.ORDERS} All Orders", callback_data="admin_all_orders")],
            [InlineKeyboardButton(text=f"{Emoji.QR} Update QR Code", callback_data="admin_update_qr")],
            [InlineKeyboardButton(text=f"{Emoji.BROADCAST} Broadcast", callback_data="admin_broadcast")],
            [InlineKeyboardButton(text=f"{Emoji.USER} Users", callback_data="admin_users")],
            [InlineKeyboardButton(text=f"{Emoji.STATS} Statistics", callback_data="admin_stats")],
            [InlineKeyboardButton(text=f"{Emoji.HOME} Main Menu", callback_data="main_menu")]
        ])
    
    @staticmethod
    def admin_categories(categories: List[Dict]) -> InlineKeyboardMarkup:
        buttons = []
        for cat in categories[:15]:
            status = "✅" if cat['is_active'] else "❌"
            buttons.append([InlineKeyboardButton(
                text=f"{status} {cat['name']} ({cat.get('coupon_count', 0)})",
                callback_data=f"admin_cat_{cat['id']}"
            )])
        buttons.append([InlineKeyboardButton(text=f"{Emoji.ADD} Add Category", callback_data="admin_add_category")])
        buttons.append([InlineKeyboardButton(text=f"{Emoji.BACK} Back", callback_data="admin_panel")])
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def admin_category_detail(category_id: int, is_active: bool) -> InlineKeyboardMarkup:
        toggle_text = "❌ Deactivate" if is_active else "✅ Activate"
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=toggle_text, callback_data=f"admin_toggle_cat_{category_id}")],
            [InlineKeyboardButton(text=f"{Emoji.DELETE} Delete", callback_data=f"admin_delete_cat_{category_id}")],
            [InlineKeyboardButton(text=f"{Emoji.BACK} Back", callback_data="admin_categories")]
        ])
    
    @staticmethod
    def admin_coupons(coupons: List[Dict]) -> InlineKeyboardMarkup:
        buttons = []
        for coupon in coupons[:15]:
            status = "✅" if coupon['is_active'] else "❌"
            buttons.append([InlineKeyboardButton(
                text=f"{status} {coupon['name']} - {Config.CURRENCY}{coupon['price']} ({coupon['available_stock']})",
                callback_data=f"admin_cpn_{coupon['id']}"
            )])
        buttons.append([InlineKeyboardButton(text=f"{Emoji.ADD} Add Coupon", callback_data="admin_add_coupon")])
        buttons.append([InlineKeyboardButton(text=f"{Emoji.BACK} Back", callback_data="admin_panel")])
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def admin_coupon_detail(coupon_id: int, is_active: bool) -> InlineKeyboardMarkup:
        toggle_text = "❌ Deactivate" if is_active else "✅ Activate"
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"{Emoji.UPLOAD} Upload Codes", callback_data=f"admin_upload_codes_{coupon_id}")],
            [InlineKeyboardButton(text=toggle_text, callback_data=f"admin_toggle_cpn_{coupon_id}")],
            [InlineKeyboardButton(text=f"{Emoji.DELETE} Delete", callback_data=f"admin_delete_cpn_{coupon_id}")],
            [InlineKeyboardButton(text=f"{Emoji.BACK} Back", callback_data="admin_coupons")]
        ])
    
    @staticmethod
    def select_category_for_coupon(categories: List[Dict]) -> InlineKeyboardMarkup:
        buttons = []
        for cat in categories:
            buttons.append([InlineKeyboardButton(
                text=f"{cat.get('icon', Emoji.CATEGORY)} {cat['name']}",
                callback_data=f"select_cat_{cat['id']}"
            )])
        buttons.append([InlineKeyboardButton(text=f"{Emoji.CROSS} Cancel", callback_data="cancel")])
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def admin_orders(orders: List[Dict], filter_type: str = "all") -> InlineKeyboardMarkup:
        buttons = []
        status_emoji = {'pending': Emoji.PENDING, 'approved': Emoji.APPROVED, 'delivered': Emoji.APPROVED, 'rejected': Emoji.REJECTED}
        for order in orders[:15]:
            emoji = status_emoji.get(order['status'], '')
            buttons.append([InlineKeyboardButton(
                text=f"{emoji} #{order['id']} - {order.get('coupon_name', 'N/A')} ({Config.CURRENCY}{order['total_price']})",
                callback_data=f"admin_order_{order['id']}"
            )])
        buttons.append([InlineKeyboardButton(text=f"{Emoji.BACK} Back", callback_data="admin_panel")])
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def order_verification(order_id: int) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📸 View Screenshot", callback_data=f"view_screenshot_{order_id}")],
            [InlineKeyboardButton(text=f"{Emoji.APPROVED} Approve", callback_data=f"approve_order_{order_id}")],
            [InlineKeyboardButton(text=f"{Emoji.REJECTED} Reject", callback_data=f"reject_order_{order_id}")],
            [InlineKeyboardButton(text=f"{Emoji.BACK} Back", callback_data="admin_pending_orders")]
        ])
    
    @staticmethod
    def back_button(callback_data: str, text: str = "Back") -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"{Emoji.BACK} {text}", callback_data=callback_data)]
        ])
    
    @staticmethod
    def cancel_button() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"{Emoji.CROSS} Cancel", callback_data="cancel")]
        ])"""Inline Keyboard Builders"""
from typing import List, Dict
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config, Emoji

class Keyboards:
    
    @staticmethod
    def main_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
        buttons = [
            [InlineKeyboardButton(text=f"{Emoji.CATEGORY} Browse Categories", callback_data="browse_categories")],
            [InlineKeyboardButton(text=f"{Emoji.ORDERS} My Orders", callback_data="my_orders")],
            [InlineKeyboardButton(text=f"{Emoji.HELP} Help", callback_data="help")]
        ]
        if is_admin:
            buttons.append([InlineKeyboardButton(text=f"{Emoji.ADMIN} Admin Panel", callback_data="admin_panel")])
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def categories_menu(categories: List[Dict]) -> InlineKeyboardMarkup:
        buttons = []
        for cat in categories:
            buttons.append([InlineKeyboardButton(
                text=f"{cat.get('icon', Emoji.CATEGORY)} {cat['name']} ({cat.get('coupon_count', 0)})",
                callback_data=f"category_{cat['id']}"
            )])
        buttons.append([InlineKeyboardButton(text=f"{Emoji.HOME} Main Menu", callback_data="main_menu")])
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def coupons_menu(coupons: List[Dict], category_id: int) -> InlineKeyboardMarkup:
        buttons = []
        for coupon in coupons:
            stock_info = f"({coupon['available_stock']} left)" if coupon['available_stock'] < 50 else ""
            buttons.append([InlineKeyboardButton(
                text=f"{coupon['name']} - {Config.CURRENCY}{coupon['price']:.2f} {stock_info}",
                callback_data=f"coupon_{coupon['id']}"
            )])
        buttons.append([InlineKeyboardButton(text=f"{Emoji.BACK} Back", callback_data="browse_categories")])
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def coupon_detail(coupon: Dict, user_id: int = None) -> InlineKeyboardMarkup:
        buttons = []
        if coupon['available_stock'] > 0:
            buttons.append([InlineKeyboardButton(text=f"{Emoji.CART} Purchase Now", callback_data=f"purchase_{coupon['id']}")])
        else:
            buttons.append([InlineKeyboardButton(text=f"{Emoji.CROSS} Out of Stock", callback_data="out_of_stock")])
        buttons.append([InlineKeyboardButton(text=f"{Emoji.BACK} Back", callback_data=f"category_{coupon['category_id']}")])
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def quantity_selector(coupon_id: int, max_qty: int) -> InlineKeyboardMarkup:
        buttons = []
        qty_row = []
        for i in range(1, min(max_qty + 1, 11)):
            qty_row.append(InlineKeyboardButton(text=str(i), callback_data=f"qty_{coupon_id}_{i}"))
            if i % 5 == 0:
                buttons.append(qty_row)
                qty_row = []
        if qty_row:
            buttons.append(qty_row)
        buttons.append([InlineKeyboardButton(text=f"{Emoji.BACK} Back", callback_data=f"coupon_{coupon_id}")])
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def payment_confirmation() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"{Emoji.CHECK} I've Paid - Submit Proof", callback_data="submit_payment")],
            [InlineKeyboardButton(text=f"{Emoji.CROSS} Cancel Order", callback_data="cancel_order")]
        ])
    
    @staticmethod
    def cancel_order() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"{Emoji.CROSS} Cancel Order", callback_data="cancel_order")]
        ])
    
    @staticmethod
    def user_orders(orders: List[Dict]) -> InlineKeyboardMarkup:
        buttons = []
        status_emoji = {'pending': Emoji.PENDING, 'approved': Emoji.APPROVED, 'delivered': Emoji.APPROVED, 'rejected': Emoji.REJECTED}
        for order in orders[:10]:
            emoji = status_emoji.get(order['status'], '')
            buttons.append([InlineKeyboardButton(
                text=f"{emoji} Order #{order['id']} - {order.get('coupon_name', 'N/A')}",
                callback_data=f"user_order_{order['id']}"
            )])
        buttons.append([InlineKeyboardButton(text=f"{Emoji.HOME} Main Menu", callback_data="main_menu")])
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def admin_panel() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"{Emoji.CATEGORY} Manage Categories", callback_data="admin_categories")],
            [InlineKeyboardButton(text=f"{Emoji.COUPON} Manage Coupons", callback_data="admin_coupons")],
            [InlineKeyboardButton(text=f"{Emoji.PENDING} Pending Orders", callback_data="admin_pending_orders")],
            [InlineKeyboardButton(text=f"{Emoji.ORDERS} All Orders", callback_data="admin_all_orders")],
            [InlineKeyboardButton(text=f"{Emoji.QR} Update QR Code", callback_data="admin_update_qr")],
            [InlineKeyboardButton(text=f"{Emoji.BROADCAST} Broadcast", callback_data="admin_broadcast")],
            [InlineKeyboardButton(text=f"{Emoji.USER} Users", callback_data="admin_users")],
            [InlineKeyboardButton(text=f"{Emoji.STATS} Statistics", callback_data="admin_stats")],
            [InlineKeyboardButton(text=f"{Emoji.HOME} Main Menu", callback_data="main_menu")]
        ])
    
    @staticmethod
    def admin_categories(categories: List[Dict]) -> InlineKeyboardMarkup:
        buttons = []
        for cat in categories[:15]:
            status = "✅" if cat['is_active'] else "❌"
            buttons.append([InlineKeyboardButton(
                text=f"{status} {cat['name']} ({cat.get('coupon_count', 0)})",
                callback_data=f"admin_cat_{cat['id']}"
            )])
        buttons.append([InlineKeyboardButton(text=f"{Emoji.ADD} Add Category", callback_data="admin_add_category")])
        buttons.append([InlineKeyboardButton(text=f"{Emoji.BACK} Back", callback_data="admin_panel")])
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def admin_category_detail(category_id: int, is_active: bool) -> InlineKeyboardMarkup:
        toggle_text = "❌ Deactivate" if is_active else "✅ Activate"
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=toggle_text, callback_data=f"admin_toggle_cat_{category_id}")],
            [InlineKeyboardButton(text=f"{Emoji.DELETE} Delete", callback_data=f"admin_delete_cat_{category_id}")],
            [InlineKeyboardButton(text=f"{Emoji.BACK} Back", callback_data="admin_categories")]
        ])
    
    @staticmethod
    def admin_coupons(coupons: List[Dict]) -> InlineKeyboardMarkup:
        buttons = []
        for coupon in coupons[:15]:
            status = "✅" if coupon['is_active'] else "❌"
            buttons.append([InlineKeyboardButton(
                text=f"{status} {coupon['name']} - {Config.CURRENCY}{coupon['price']} ({coupon['available_stock']})",
                callback_data=f"admin_cpn_{coupon['id']}"
            )])
        buttons.append([InlineKeyboardButton(text=f"{Emoji.ADD} Add Coupon", callback_data="admin_add_coupon")])
        buttons.append([InlineKeyboardButton(text=f"{Emoji.BACK} Back", callback_data="admin_panel")])
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def admin_coupon_detail(coupon_id: int, is_active: bool) -> InlineKeyboardMarkup:
        toggle_text = "❌ Deactivate" if is_active else "✅ Activate"
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"{Emoji.UPLOAD} Upload Codes", callback_data=f"admin_upload_codes_{coupon_id}")],
            [InlineKeyboardButton(text=toggle_text, callback_data=f"admin_toggle_cpn_{coupon_id}")],
            [InlineKeyboardButton(text=f"{Emoji.DELETE} Delete", callback_data=f"admin_delete_cpn_{coupon_id}")],
            [InlineKeyboardButton(text=f"{Emoji.BACK} Back", callback_data="admin_coupons")]
        ])
    
    @staticmethod
    def select_category_for_coupon(categories: List[Dict]) -> InlineKeyboardMarkup:
        buttons = []
        for cat in categories:
            buttons.append([InlineKeyboardButton(
                text=f"{cat.get('icon', Emoji.CATEGORY)} {cat['name']}",
                callback_data=f"select_cat_{cat['id']}"
            )])
        buttons.append([InlineKeyboardButton(text=f"{Emoji.CROSS} Cancel", callback_data="cancel")])
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def admin_orders(orders: List[Dict], filter_type: str = "all") -> InlineKeyboardMarkup:
        buttons = []
        status_emoji = {'pending': Emoji.PENDING, 'approved': Emoji.APPROVED, 'delivered': Emoji.APPROVED, 'rejected': Emoji.REJECTED}
        for order in orders[:15]:
            emoji = status_emoji.get(order['status'], '')
            buttons.append([InlineKeyboardButton(
                text=f"{emoji} #{order['id']} - {order.get('coupon_name', 'N/A')} ({Config.CURRENCY}{order['total_price']})",
                callback_data=f"admin_order_{order['id']}"
            )])
        buttons.append([InlineKeyboardButton(text=f"{Emoji.BACK} Back", callback_data="admin_panel")])
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def order_verification(order_id: int) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📸 View Screenshot", callback_data=f"view_screenshot_{order_id}")],
            [InlineKeyboardButton(text=f"{Emoji.APPROVED} Approve", callback_data=f"approve_order_{order_id}")],
            [InlineKeyboardButton(text=f"{Emoji.REJECTED} Reject", callback_data=f"reject_order_{order_id}")],
            [InlineKeyboardButton(text=f"{Emoji.BACK} Back", callback_data="admin_pending_orders")]
        ])
    
    @staticmethod
    def back_button(callback_data: str, text: str = "Back") -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"{Emoji.BACK} {text}", callback_data=callback_data)]
        ])
    
    @staticmethod
    def cancel_button() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"{Emoji.CROSS} Cancel", callback_data="cancel")]
        ])