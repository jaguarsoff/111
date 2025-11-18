
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

import db, utils, keyboards
from config import BOT_TOKEN, ADMIN_ID

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()

class AddItemStates(StatesGroup):
    title = State()
    price = State()
    weight = State()
    qty = State()
    category = State()

class ContactState(StatesGroup):
    phone = State()

# ---- START ----

@dp.message(Command("start"))
async def cmd_start(msg: Message):
    db.init_db()
    await msg.answer(
        "<b>Добро пожаловать 👋</b>"
        "Я помогу заказать товары из Poizon максимально удобно.
"
        "Выберите действие в меню ниже:",
        reply_markup=keyboards.main_kb(msg.from_user.id == ADMIN_ID)
    )

# ---- HELP ----

@dp.callback_query(F.data == "help")
async def cb_help(cq: CallbackQuery):
    await cq.message.edit_text(
        "<b>📝 Помощь</b>"
        "• Добавьте товары в корзину через «Каталог».
"
        "• Проверьте содержимое корзины.
"
        "• Нажмите <b>/checkout</b> для оформления.
"
        "• Первый заказ попросит контакт — сохранится навсегда.
"
        "• После оформления админ свяжется с вами.
"
        "• Статус заказа будет обновляться автоматически.
",
        reply_markup=keyboards.main_kb(cq.from_user.id == ADMIN_ID)
    )
    await cq.answer()

# ---- CATALOG ADD ITEM ----

@dp.callback_query(F.data == "catalog")
async def cb_catalog(cq: CallbackQuery, state: FSMContext):
    await state.clear()
    await cq.message.edit_text(
        "<b>Добавление товара 🛒</b>

Введите название товара:"
    )
    await AddItemStates.title.set()
    await cq.answer()

@dp.message(AddItemStates.title)
async def add_title(msg: Message, state: FSMContext):
    await state.update_data(title=msg.text)
    await msg.answer("Введите цену товара в CNY:")
    await AddItemStates.price.set()

@dp.message(AddItemStates.price)
async def add_price(msg: Message, state: FSMContext):
    try:
        v = float(msg.text.replace(",", "."))
    except:
        return await msg.reply("❗ Введите корректное число")
    await state.update_data(price=v)
    await msg.answer("Введите вес товара в кг (например 0.8):")
    await AddItemStates.weight.set()

@dp.message(AddItemStates.weight)
async def add_weight(msg: Message, state: FSMContext):
    try:
        v = float(msg.text.replace(",", "."))
    except:
        return await msg.reply("❗ Введите корректный вес")
    await state.update_data(weight=v)
    await msg.answer("Количество товара:")
    await AddItemStates.qty.set()

@dp.message(AddItemStates.qty)
async def add_qty(msg: Message, state: FSMContext):
    try:
        v = int(msg.text)
    except:
        return await msg.reply("❗ Введите целое число")
    await state.update_data(qty=v)
    await msg.answer("Категория товара (shoes / clothes / other):")
    await AddItemStates.category.set()

@dp.message(AddItemStates.category)
async def add_category(msg: Message, state: FSMContext):
    data = await state.get_data()
    db.add_to_cart(
        msg.from_user.id,
        data["title"],
        data["price"],
        data["weight"],
        data["qty"],
        msg.text,
        ""
    )
    await msg.answer(
        "✔ Товар добавлен в корзину!
"
        "Можете добавить ещё или открыть корзину через кнопку «🧺 Корзина»."
    )
    await state.clear()

# ---- CART ----

@dp.callback_query(F.data == "cart")
async def cb_cart(cq: CallbackQuery):
    items = db.get_cart(cq.from_user.id)
    if not items:
        return await cq.message.edit_text(
            "🧺 <b>Ваша корзина пуста</b>",
            reply_markup=keyboards.main_kb(cq.from_user.id == ADMIN_ID)
        )

    text = "<b>🧺 Ваша корзина:</b>

"
    for it in items:
        text += (
            f"<b>ID {it['id']}:</b> {it['title']}
"
            f"Цена: {it['price_cny']} CNY × {it['qty']}
"
            f"Вес: {it['weight_kg']} кг
"
            f"Категория: {it['category']}
"
            "——————————————
"
        )
    text += "
Чтобы оформить заказ — используйте команду /checkout"

    await cq.message.edit_text(
        text,
        reply_markup=keyboards.main_kb(cq.from_user.id == ADMIN_ID)
    )
    await cq.answer()

# ---- DELETE ITEM ----

@dp.callback_query(F.data.startswith("cart_delete:"))
async def cb_cart_delete(cq: CallbackQuery):
    iid = int(cq.data.split(":")[1])
    db.remove_cart_item(iid, cq.from_user.id)
    await cq.answer("Удалено")
    await cb_cart(cq)

# ---- CALC ----

@dp.callback_query(F.data == "calc")
async def cb_calc(cq: CallbackQuery):
    items = db.get_cart(cq.from_user.id)
    if not items:
        return await cq.message.edit_text(
            "В корзине нет товаров.",
            reply_markup=keyboards.main_kb(cq.from_user.id == ADMIN_ID)
        )

    r = utils.calc_order(items)
    text = (
        "<b>💰 Расчёт стоимости:</b>
"
        f"📦 Вес: <b>{r['total_weight']} кг</b>
"
        f"🛒 Товары: <b>{r['items_cost']} руб</b>
"
        f"🚚 Доставка: <b>{r['shipping']} руб</b>

"
        f"💵 <b>Итого: {r['total']} руб</b>
"
        "⏳ Срок доставки: <b>2–3.5 недели</b>
"
    )
    await cq.message.edit_text(
        text, reply_markup=keyboards.main_kb(cq.from_user.id == ADMIN_ID)
    )
    await cq.answer()

# ---- MY ORDERS ----

@dp.callback_query(F.data == "my_orders")
async def cb_my_orders(cq: CallbackQuery):
    all_orders = db.list_orders()
    user_orders = [o for o in all_orders if o["user_id"] == cq.from_user.id]

    if not user_orders:
        return await cq.message.edit_text(
            "У вас ещё нет заказов.",
            reply_markup=keyboards.main_kb(cq.from_user.id == ADMIN_ID)
        )

    text = "<b>📦 Мои заказы:</b>
"
    for o in user_orders:
        text += (
            f"№{o['id']} • {o['status']}
"
            f"Сумма: {o['total_rub']} руб
"
            f"{o['created_at']}
"
            "————————————
"
        )
    await cq.message.edit_text(
        text,
        reply_markup=keyboards.main_kb(cq.from_user.id == ADMIN_ID)
    )
    await cq.answer()

# ---- CHECKOUT ----

@dp.message(Command("checkout"))
async def cmd_checkout(msg: Message, state: FSMContext):
    items = db.get_cart(msg.from_user.id)
    if not items:
        return await msg.reply("Корзина пуста.")

    user = db.get_user(msg.from_user.id)
    if not user or not user.get("phone"):
        await msg.reply(
            "📱 Введите ваш номер телефона для оформления заказа:"
        )
        await ContactState.phone.set()
        return

    r = utils.calc_order(items)
    text = (
        "<b>Подтвердите оформление заказа:</b>
"
        f"📦 Вес: {r['total_weight']} кг
"
        f"🛒 Товары: {r['items_cost']} руб
"
        f"🚚 Доставка: {r['shipping']} руб
"
        f"💵 <b>Итого: {r['total']} руб</b>
"
    )
    await msg.answer(text + "Нажмите кнопку ниже:", reply_markup=keyboards.confirm_order_kb())

@dp.callback_query(F.data == "confirm_order")
async def confirm_order(cq: CallbackQuery):
    user = db.get_user(cq.from_user.id)
    items = db.get_cart(cq.from_user.id)
    r = utils.calc_order(items)

    oid = db.create_order_from_cart(
        cq.from_user.id, r["total"], user["phone"], datetime.utcnow().isoformat()
    )

    await bot.send_message(
        ADMIN_ID,
        f"🔔 Новый заказ!

<b>№{oid}</b>
"
        f"Пользователь: {cq.from_user.id}
"
        f"Сумма: {r['total']} руб
"
    )

    await cq.message.edit_text(
        f"🎉 <b>Заказ №{oid} оформлен!</b>
Админ скоро свяжется с вами для оплаты."
    )
    await cq.answer()

# ---- CONTACT SAVE ----

@dp.message(ContactState.phone)
async def save_contact(msg: Message, state: FSMContext):
    phone = msg.text.strip()
    db.save_user_contact(msg.from_user.id, msg.from_user.username or "", phone)
    await state.clear()
    await msg.reply(
        "📱 Контакт сохранён!
Теперь можете снова выполнить /checkout"
    )

# ---- ADMIN ----

@dp.callback_query(F.data == "admin")
async def admin_panel(cq: CallbackQuery):
    if cq.from_user.id != ADMIN_ID:
        return await cq.answer("Нет доступа", show_alert=True)

    await cq.message.edit_text(
        "<b>🔧 Админ-панель</b>
"
        "Доступные команды:
"
        "• /orders — Все заказы
"
        "• /setstatus <id> <status> — изменить статус",
        reply_markup=keyboards.main_kb(True)
    )
    await cq.answer()

@dp.message(Command("orders"))
async def admin_orders(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        return await msg.reply("Нет доступа.")

    orders = db.list_orders()
    if not orders:
        return await msg.reply("Заказов нет.")

    text = "<b>Список заказов:</b>

"
    for o in orders:
        text += (
            f"№{o['id']} — {o['status']}
"
            f"{o['total_rub']} руб
"
            f"{o['created_at']}
"
            "————————————
"
        )
    await msg.reply(text)

@dp.message()
async def admin_setstatus(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        return

    if not msg.text.startswith("/setstatus"):
        return

    p = msg.text.split(maxsplit=2)
    if len(p) < 3:
        return await msg.reply("Использование: /setstatus <id> <status>")

    oid = int(p[1])
    status = p[2]

    db.set_order_status(oid, status)
    order = db.get_order(oid)

    await bot.send_message(
        order["user_id"],
        f"🔄 Статус вашего заказа №{oid} обновлён:
<b>{status}</b>"
    )
    await msg.reply("Статус обновлён.")

async def main():
    import logging
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
