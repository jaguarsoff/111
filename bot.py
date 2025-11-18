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


# -------------------- STATES --------------------

class AddItemStates(StatesGroup):
    title = State()
    price = State()
    weight = State()
    qty = State()
    category = State()

class ContactState(StatesGroup):
    phone = State()


# -------------------- START --------------------

@dp.message(Command("start"))
async def cmd_start(msg: Message):
    db.init_db()
    await msg.answer(
        "<b>Добро пожаловать 👋</b>\n"
        "Я помогу заказать товары из Poizon максимально удобно.\n\n"
        "Выберите действие в меню ниже:",
        reply_markup=keyboards.main_kb(msg.from_user.id == ADMIN_ID)
    )


# -------------------- HELP --------------------

@dp.callback_query(F.data == "help")
async def cb_help(cq: CallbackQuery):
    await cq.message.edit_text(
        "<b>📝 Помощь</b>\n\n"
        "• Добавьте товары в корзину через «Каталог».\n"
        "• Проверьте содержимое корзины.\n"
        "• Нажмите <b>/checkout</b> для оформления.\n"
        "• Первый заказ попросит контакт — сохранится навсегда.\n"
        "• После оформления админ свяжется с вами.\n"
        "• Статус заказа будет обновляться автоматически.",
        reply_markup=keyboards.main_kb(cq.from_user.id == ADMIN_ID)
    )
    await cq.answer()


# -------------------- CATALOG ADD ITEM --------------------

@dp.callback_query(F.data == "catalog")
async def cb_catalog(cq: CallbackQuery, state: FSMContext):
    await state.clear()
    await cq.message.edit_text(
        "<b>Добавление товара 🛒</b>\n"
        "Введите название товара:"
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
        return await msg.reply("❗ Введите корректное число (пример: 599)")
    await state.update_data(price=v)
    await msg.answer("Введите вес товара в кг (например: 0.8):")
    await AddItemStates.weight.set()


@dp.message(AddItemStates.weight)
async def add_weight(msg: Message, state: FSMContext):
    try:
        v = float(msg.text.replace(",", "."))
    except:
        return await msg.reply("❗ Введите корректный вес (пример: 0.6)")
    await state.update_data(weight=v)
    await msg.answer("Количество товара (целое число):")
    await AddItemStates.qty.set()


@dp.message(AddItemStates.qty)
async def add_qty(msg: Message, state: FSMContext):
    try:
        v = int(msg.text)
    except:
        return await msg.reply("❗ Введите целое число (пример: 2)")
    await state.update_data(qty=v)
    await msg.answer("Категория товара:\n\n"
                     "<b>shoes</b> — обувь\n"
                     "<b>clothes</b> — одежда\n"
                     "<b>other</b> — другое\n\n"
                     "Введите категорию:")
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
        msg.text.lower(),
        ""
    )

    await msg.answer(
        "✔ <b>Товар добавлен в корзину!</b>\n"
        "Вы можете добавить ещё товары или открыть корзину через кнопку <b>🧺 Корзина</b>.",
        reply_markup=keyboards.main_kb(msg.from_user.id == ADMIN_ID)
    )

    await state.clear()


# -------------------- CART --------------------

@dp.callback_query(F.data == "cart")
async def cb_cart(cq: CallbackQuery):
    items = db.get_cart(cq.from_user.id)
    if not items:
        return await cq.message.edit_text(
            "🧺 <b>Ваша корзина пуста</b>",
            reply_markup=keyboards.main_kb(cq.from_user.id == ADMIN_ID)
        )

    text = "<b>🧺 Ваша корзина:</b>\n\n"

    for it in items:
        text += (
            f"<b>ID {it['id']}</b>\n"
            f"📌 {it['title']}\n"
            f"💵 Цена: {it['price_cny']} CNY × {it['qty']}\n"
            f"⚖ Вес: {it['weight_kg']} кг\n"
            f"🏷 Категория: {it['category']}\n"
            "——————————————\n"
        )

    text += "\nЧтобы оформить заказ — используйте команду <b>/checkout</b>"

    await cq.message.edit_text(
        text,
        reply_markup=keyboards.main_kb(cq.from_user.id == ADMIN_ID)
    )
    await cq.answer()


# -------------------- DELETE ITEM --------------------

@dp.callback_query(F.data.startswith("cart_delete:"))
async def cb_cart_delete(cq: CallbackQuery):
    iid = int(cq.data.split(":")[1])
    db.remove_cart_item(iid, cq.from_user.id)
    await cq.answer("Удалено")
    await cb_cart(cq)


# -------------------- CALC --------------------

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
        "<b>💰 Расчёт стоимости:</b>\n\n"
        f"📦 Общий вес: <b>{r['total_weight']} кг</b>\n"
        f"🛒 Стоимость товаров: <b>{r['items_cost']} руб</b>\n"
        f"🚚 Доставка: <b>{r['shipping']} руб</b>\n\n"
        f"💵 <b>Итого к оплате: {r['total']} руб</b>\n\n"
        "⏳ Срок доставки: <b>2–3.5 недели</b>"
    )

    await cq.message.edit_text(
        text,
        reply_markup=keyboards.main_kb(cq.from_user.id == ADMIN_ID)
    )
    await cq.answer()


# -------------------- MY ORDERS --------------------

@dp.callback_query(F.data == "my_orders")
async def cb_my_orders(cq: CallbackQuery):
    all_orders = db.list_orders()
    user_orders = [o for o in all_orders if o["user_id"] == cq.from_user.id]

    if not user_orders:
        return await cq.message.edit_text(
            "У вас ещё нет заказов.",
            reply_markup=keyboards.main_kb(cq.from_user.id == ADMIN_ID)
        )

    text = "<b>📦 Мои заказы:</b>\n\n"

    for o in user_orders:
        text += (
            f"№{o['id']} — <b>{o['status']}</b>\n"
            f"Сумма: {o['total_rub']} руб\n"
            f"🕒 {o['created_at']}\n"
            "————————————\n"
        )

    await cq.message.edit_text(
        text,
        reply_markup=keyboards.main_kb(cq.from_user.id == ADMIN_ID)
    )
    await cq.answer()


# -------------------- CHECKOUT --------------------

@dp.message(Command("checkout"))
async def cmd_checkout(msg: Message, state: FSMContext):
    items = db.get_cart(msg.from_user.id)

    if not items:
        return await msg.reply("Корзина пуста.")

    user = db.get_user(msg.from_user.id)

    if not user or not user.get("phone"):
        await msg.reply("📱 Введите ваш номер телефона для оформления заказа:")
        await ContactState.phone.set()
        return

    r = utils.calc_order(items)

    text = (
        "<b>Подтвердите оформление заказа:</b>\n\n"
        f"📦 Вес: {r['total_weight']} кг\n"
        f"🛒 Товары: {r['items_cost']} руб\n"
        f"🚚 Доставка: {r['shipping']} руб\n\n"
        f"💵 <b>Итого: {r['total']} руб</b>\n"
    )

    await msg.answer(text, reply_markup=keyboards.confirm_order_kb())


@dp.callback_query(F.data == "confirm_order")
async def confirm_order(cq: CallbackQuery):
    user = db.get_user(cq.from_user.id)
    items = db.get_cart(cq.from_user.id)
    r = utils.calc_order(items)

    oid = db.create_order_from_cart(
        cq.from_user.id,
        r["total"],
        user["phone]()
