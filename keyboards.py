
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def main_kb(is_admin=False):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🛍 Каталог", callback_data="catalog"),
        InlineKeyboardButton("🧺 Корзина", callback_data="cart"),
    )
    kb.add(
        InlineKeyboardButton("💰 Расчёт", callback_data="calc"),
        InlineKeyboardButton("📦 Мои заказы", callback_data="my_orders")
    )
    kb.add(InlineKeyboardButton("❓ Помощь", callback_data="help"))
    if is_admin:
        kb.add(InlineKeyboardButton("🔧 Админ-панель", callback_data="admin"))
    return kb

def cart_item_kb(item_id):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✏️ Изменить", callback_data=f"cart_edit:{item_id}"),
        InlineKeyboardButton("🗑 Удалить", callback_data=f"cart_delete:{item_id}")
    )
    kb.add(InlineKeyboardButton("⬅ Назад", callback_data="cart"))
    return kb

def confirm_order_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ Подтвердить заказ", callback_data="confirm_order"),
        InlineKeyboardButton("⬅ Назад", callback_data="cart")
    )
    return kb
