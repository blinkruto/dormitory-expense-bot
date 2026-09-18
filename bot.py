
from database import (
    create_db,
    add_expense,
    get_expenses,
    get_balance,
    create_users_table,
    add_user,
    get_users,
    get_settlement_data,
    create_archive_table,
    archive_and_clear_expenses,
    get_archive
)
import asyncio
import os
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from dotenv import load_dotenv


load_dotenv()

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("Не найден BOT_TOKEN в файле .env")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="➕ Добавить расход"),
            KeyboardButton(text="💰 Баланс")
        ],
        [
            KeyboardButton(text="🧮 Рассчитать долги"),
            KeyboardButton(text="📋 История")
        ],
        [
            KeyboardButton(text="📦 Архив")
        ]
    ],
    resize_keyboard=True
)
class AddExpense(StatesGroup):
    amount = State()
    description = State()

create_db()
create_users_table()
create_archive_table()

@dp.message(Command("join"))
async def join_handler(message: Message):
    add_user(
        message.from_user.id,
        message.from_user.first_name
    )

    await message.answer(
        f"{message.from_user.first_name}, ты добавлен в общий расчёт."
    )
@dp.message(Command("settle"))
async def settle_handler(message: Message):
    data = get_settlement_data()

    if len(data) < 2:
        await message.answer("Недостаточно участников.")
        return

    total = sum(amount for _, _, amount in data)
    average = total / len(data)

    debtors = []
    creditors = []

    for user_id, username, amount in data:
        balance = amount - average

        if balance < -0.01:
            debtors.append([username, -balance])

        elif balance > 0.01:
            creditors.append([username, balance])

    payments = []

    i = 0
    j = 0

    while i < len(debtors) and j < len(creditors):

        debtor_name, debt = debtors[i]
        creditor_name, credit = creditors[j]

        payment = min(debt, credit)

        payments.append(
            f"{debtor_name} → {creditor_name}: {payment:.2f} ₽"
        )

        debtors[i][1] -= payment
        creditors[j][1] -= payment

        if debtors[i][1] < 0.01:
            i += 1

        if creditors[j][1] < 0.01:
            j += 1

    text = (
        f"Всего потрачено: {total:.2f} ₽\n"
        f"На человека: {average:.2f} ₽\n\n"
        "Переводы:\n"
    )

    if payments:
        text += "\n".join(payments)
    else:
        text += "Никто никому ничего не должен."

    await message.answer(text)


@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "👋 Добро пожаловать!\n\n"
        "Этот бот ведёт общий учёт расходов на продукты в нашей комнате.\n\n"
        "Как это работает:\n"
        "1. Добавься в общий расчёт командой /join\n"
        "2. Купил продукты на всех — нажми «➕ Добавить расход»\n"
        "3. Введи сумму покупки\n"
        "4. Напиши, что именно ты купил\n"
        "5. «💰 Баланс» показывает расходы каждого\n"
        "6. «🧮 Рассчитать долги» показывает, кто кому должен\n\n"
        "Пример:\n"
        "➕ Добавить расход\n"
        "1500\n"
        "мясо, макароны и овощи\n\n"
        "Чтобы начать участие, напиши /join",
        reply_markup=menu
    )
@dp.message(lambda message: message.text == "➕ Добавить расход")
async def add_button(message: Message, state: FSMContext):
    await message.answer("Сколько ты потратил?")
    await state.set_state(AddExpense.amount)



@dp.message(lambda message: message.text == "💰 Баланс")
async def balance_button(message: Message, state: FSMContext):
    await state.clear()
    await balance(message)


@dp.message(lambda message: message.text == "🧮 Рассчитать долги")
async def settle_button(message: Message, state: FSMContext):
    await state.clear()
    await settle_handler(message)


@dp.message(lambda message: message.text == "📋 История")
async def history_button(message: Message, state: FSMContext):
    await state.clear()
    await history(message)


@dp.message(lambda message: message.text == "📦 Архив")
async def archive_button(message: Message, state: FSMContext):
    await state.clear()
    await archive_handler(message)

@dp.message(Command("add"))
async def add_expense_handler(message: Message):
    parts = message.text.split(maxsplit=2)

    if len(parts) < 2:
        await message.answer("Используй так: /add 1250 продукты")
        return

    try:
        amount = float(parts[1])
    except ValueError:
        await message.answer("Сумма должна быть числом.")
        return

    description = parts[2] if len(parts) > 2 else "Без описания"

    add_expense(
        message.from_user.id,
        message.from_user.first_name,
        amount,
        description
    )

    await message.answer(
        f"Записал расход:\n"
        f"{amount:.2f} ₽\n"
        f"{description}"
    )

@dp.message(Command("history"))
async def history(message: Message):
    expenses = get_expenses()

    if not expenses:
        await message.answer("Расходов пока нет.")
        return

    text = "История расходов:\n\n"

    for username, amount, description in expenses:
        text += f"{username}: {amount:.2f} ₽ — {description}\n"

    await message.answer(text)

async def main():
    await dp.start_polling(bot)

@dp.message(Command("balance"))
async def balance(message: Message):
    balances = get_balance()

    if not balances:
        await message.answer("Расходов пока нет.")
        return

    text = "Расходы:\n\n"

    total = 0

    for username, amount in balances:
        text += f"{username}: {amount:.2f} ₽\n"
        total += amount

    text += f"\nВсего: {total:.2f} ₽"

    await message.answer(text)

@dp.message(Command("reset"))
async def reset_handler(message: Message):
    parts = message.text.split()

    if len(parts) != 2 or parts[1].lower() != "confirm":
        await message.answer(
            "Текущий период будет отправлен в архив.\n\n"
            "Для подтверждения напиши:\n"
            "/reset confirm"
        )
        return

    period_id = archive_and_clear_expenses()

    await message.answer(
        f"Период {period_id} сохранён в архив.\n"
        f"Текущие расходы обнулены."
    )

@dp.message(Command("archive"))
async def archive_handler(message: Message):
    rows = get_archive()

    if not rows:
        await message.answer("Архив пока пуст.")
        return

    text = "Архив расходов:\n\n"

    current_period = None

    for period_id, username, amount, description in rows:

        if period_id != current_period:
            text += f"\nПериод: {period_id}\n"
            current_period = period_id

        text += f"{username}: {amount:.2f} ₽ — {description}\n"

    await message.answer(text)

@dp.message(AddExpense.amount)
async def get_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Введи сумму числом. Например: 1500")
        return

    if amount <= 0:
        await message.answer("Сумма должна быть больше 0.")
        return

    await state.update_data(amount=amount)

    await message.answer("Что ты купил?")
    await state.set_state(AddExpense.description)


@dp.message(AddExpense.description)
async def get_description(message: Message, state: FSMContext):
    data = await state.get_data()

    amount = data["amount"]
    description = message.text

    add_expense(
        message.from_user.id,
        message.from_user.first_name,
        amount,
        description
    )

    await message.answer(
        f"✅ Записал\n"
        f"{amount:.2f} ₽ — {description}",
        reply_markup=menu
    )

    await state.clear()

@dp.message(Command("users"))
async def users_handler(message: Message):
    users = get_users()

    if not users:
        await message.answer("Пока никто не зарегистрирован.")
        return

    text = f"Участников: {len(users)}\n\n"

    for user_id, username in users:
        text += f"• {username}\n"

    await message.answer(text)

if __name__ == "__main__":
    asyncio.run(main())