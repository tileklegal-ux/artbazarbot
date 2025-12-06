from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from roles_db import is_owner, is_manager
from navigation import go_main_menu, navigation_kb
from premium_db import set_premium

router = Router()


# ---------- КЛАВИАТУРЫ ----------

owner_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Выдать премиум 🎁")],
        [KeyboardButton(text="🏠 Главное меню")]
    ],
    resize_keyboard=True
)

manager_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Выдать премиум 🎁")],
        [KeyboardButton(text="🏠 Главное меню")]
    ],
    resize_keyboard=True
)


# ---------- FSM для выдачи премиума ----------

class PremiumFSM(StatesGroup):
    waiting_user_id = State()
    waiting_tariff = State()


# ---------- ВХОД В ПАНЕЛЬ ----------

@router.message(F.text == "Админ 👑")
async def owner_panel(message: Message):
    if not is_owner(message.from_user.id):
        return
    await message.answer("Панель владельца:", reply_markup=owner_kb)


@router.message(F.text == "Менеджер 📋")
async def manager_panel(message: Message):
    if not is_manager(message.from_user.id):
        return
    await message.answer("Панель менеджера:", reply_markup=manager_kb)


# ---------- ВЫДАЧА ПРЕМИУМА ----------

@router.message(F.text == "Выдать премиум 🎁")
async def start_premium(message: Message, state: FSMContext):
    if not (is_owner(message.from_user.id) or is_manager(message.from_user.id)):
        return

    await state.set_state(PremiumFSM.waiting_user_id)
    await message.answer("Введите ID пользователя:", reply_markup=navigation_kb)


@router.message(PremiumFSM.waiting_user_id, F.text == "⬅️ Назад")
async def back_from_userid(message: Message, state: FSMContext):
    await state.clear()
    await go_main_menu(message)


@router.message(PremiumFSM.waiting_user_id)
async def premium_userid(message: Message, state: FSMContext):
    try:
        uid = int(message.text)
    except:
        await message.answer("ID должно быть числом.")
        return

    await state.update_data(uid=uid)
    await state.set_state(PremiumFSM.waiting_tariff)

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="1 месяц")],
            [KeyboardButton(text="6 месяцев")],
            [KeyboardButton(text="12 месяцев")],
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True
    )

    await message.answer("Выберите тариф:", reply_markup=kb)


@router.message(PremiumFSM.waiting_tariff, F.text == "⬅️ Назад")
async def back_from_tariff(message: Message, state: FSMContext):
    await start_premium(message, state)


@router.message(PremiumFSM.waiting_tariff)
async def premium_choose_tariff(message: Message, state: FSMContext):
    tariff_map = {
        "1 месяц": 30,
        "6 месяцев": 180,
        "12 месяцев": 365
    }

    if message.text not in tariff_map:
        await message.answer("Выберите кнопку.")
        return

    days = tariff_map[message.text]
    data = await state.get_data()
    uid = data["uid"]

    until = set_premium(uid, days, message.text)

    await state.clear()

    await message.answer(
        f"Премиум выдан пользователю {uid}\n"
        f"Тариф: {message.text}\n"
        f"Действует до: <b>{until}</b>",
        parse_mode="HTML",
        reply_markup=manager_kb if is_manager(message.from_user.id) else owner_kb
    )


# ---------- ГЛАВНОЕ МЕНЮ ----------

@router.message(F.text == "🏠 Главное меню")
async def back_to_menu(message: Message):
    await go_main_menu(message)
