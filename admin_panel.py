from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from admin_keyboards import owner_admin_kb, manager_admin_kb, premium_tariff_kb
from keyboards import get_main_keyboard
from roles_db import (
    is_owner,
    is_manager,
    set_role,
    list_managers,
    get_role,
    ROLE_MANAGER,
)
from premium_db import (
    has_active_premium,
    get_premium,
    set_premium,
    list_premium_users,
)
from utils import get_text

router = Router()


class AdminStates(StatesGroup):
    await_premium_user_id = State()
    await_premium_tariff = State()
    await_add_manager_user_id = State()


# ---------- вход в панель ----------


@router.message(F.text == "Админ 👑")
async def enter_admin_panel(message: Message, state: FSMContext):
    user_id = message.from_user.id

    if not is_manager(user_id) and not is_owner(user_id):
        await message.answer(get_text(user_id, "admin_no_rights"))
        return

    await state.clear()

    if is_owner(user_id):
        text = get_text(user_id, "admin_owner_title")
        kb = owner_admin_kb
    else:
        text = get_text(user_id, "admin_manager_title")
        kb = manager_admin_kb

    await message.answer(text, reply_markup=kb)


# ---------- выход в главное меню ----------


@router.message(F.text == "⬅️ В главное меню")
async def admin_back_to_main(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await state.clear()
    role = get_role(user_id)
    kb = get_main_keyboard(role)
    await message.answer(get_text(user_id, "welcome"), reply_markup=kb)


@router.message(F.text == "⬅️ В админку")
async def back_to_admin_from_child(message: Message, state: FSMContext):
    """Возврат в админку из вложенных состояний (выбор тарифа и т.п.)."""
    user_id = message.from_user.id

    if not is_manager(user_id) and not is_owner(user_id):
        await message.answer(get_text(user_id, "admin_no_rights"))
        await state.clear()
        return

    await state.clear()

    if is_owner(user_id):
        text = get_text(user_id, "admin_owner_title")
        kb = owner_admin_kb
    else:
        text = get_text(user_id, "admin_manager_title")
        kb = manager_admin_kb

    await message.answer(text, reply_markup=kb)


# ---------- выдача премиума ----------


@router.message(F.text == "Выдать премиум 🎁")
async def admin_premium_start(message: Message, state: FSMContext):
    user_id = message.from_user.id

    if not is_manager(user_id) and not is_owner(user_id):
        await message.answer(get_text(user_id, "admin_no_rights"))
        return

    await state.set_state(AdminStates.await_premium_user_id)
    await message.answer(
        get_text(user_id, "admin_premium_prompt_user_id"),
        parse_mode="Markdown",
    )


@router.message(AdminStates.await_premium_user_id)
async def admin_premium_user_id(message: Message, state: FSMContext):
    user_id = message.from_user.id

    if not is_manager(user_id) and not is_owner(user_id):
        await message.answer(get_text(user_id, "admin_no_rights"))
        await state.clear()
        return

    text = message.text.strip()
    try:
        target_id = int(text)
    except ValueError:
        await message.answer(get_text(user_id, "admin_invalid_user_id"))
        return

    await state.update_data(target_id=target_id)
    await state.set_state(AdminStates.await_premium_tariff)
    await message.answer(
        get_text(user_id, "admin_premium_prompt_tariff"),
        reply_markup=premium_tariff_kb,
    )


@router.message(AdminStates.await_premium_tariff)
async def admin_premium_tariff(message: Message, state: FSMContext):
    user_id = message.from_user.id

    if not is_manager(user_id) and not is_owner(user_id):
        await message.answer(get_text(user_id, "admin_no_rights"))
        await state.clear()
        return

    tariff_text = message.text.strip()
    days = None

    if tariff_text == "1 месяц":
        days = 30
    elif tariff_text == "6 месяцев":
        days = 180
    elif tariff_text == "1 год":
        days = 365

    if days is None:
        await message.answer(get_text(user_id, "admin_invalid_tariff"))
        return

    data = await state.get_data()
    target_id = data.get("target_id")
    if target_id is None:
        await message.answer(get_text(user_id, "admin_invalid_user_id"))
        await state.clear()
        return

    set_premium(target_id, days=days, tariff=tariff_text)

    prem = get_premium(target_id)
    if prem:
        until_ts, _ = prem
        dt_str = datetime.fromtimestamp(until_ts).strftime("%d.%m.%Y")
    else:
        dt_str = "—"

    confirm_text = get_text(user_id, "admin_premium_set_success").format(
        user_id=target_id,
        date=dt_str,
        tariff=tariff_text,
    )

    await message.answer(confirm_text, parse_mode="Markdown")

    # Возвращаемся в админку
    await state.clear()
    if is_owner(user_id):
        kb = owner_admin_kb
        title = get_text(user_id, "admin_owner_title")
    else:
        kb = manager_admin_kb
        title = get_text(user_id, "admin_manager_title")

    await message.answer(title, reply_markup=kb)


# ---------- список премиум-пользователей ----------


@router.message(F.text == "Список премиум 👥")
async def admin_list_premium_cmd(message: Message):
    user_id = message.from_user.id

    if not is_manager(user_id) and not is_owner(user_id):
        await message.answer(get_text(user_id, "admin_no_rights"))
        return

    rows = list_premium_users(active_only=True, limit=50)

    if not rows:
        await message.answer(get_text(user_id, "admin_premium_list_empty"))
        return

    lines = [get_text(user_id, "admin_premium_list_title"), ""]
    now_ts = datetime.now().timestamp()

    for uid, until_ts, tariff in rows:
        dt_str = datetime.fromtimestamp(until_ts).strftime("%d.%m.%Y")
        days_left = max(0, int((until_ts - now_ts) // 86400))
        lines.append(f"- {uid}: до {dt_str} ({days_left} дн.), тариф: {tariff}")

    await message.answer("\n".join(lines))


# ---------- управление менеджерами (только владелец) ----------


@router.message(F.text == "Добавить менеджера ➕")
async def admin_add_manager_start(message: Message, state: FSMContext):
    user_id = message.from_user.id

    if not is_owner(user_id):
        await message.answer(get_text(user_id, "admin_not_owner"))
        return

    await state.set_state(AdminStates.await_add_manager_user_id)
    await message.answer(
        get_text(user_id, "admin_prompt_add_manager_user_id"),
        parse_mode="Markdown",
    )


@router.message(AdminStates.await_add_manager_user_id)
async def admin_add_manager_user_id(message: Message, state: FSMContext):
    user_id = message.from_user.id

    if not is_owner(user_id):
        await message.answer(get_text(user_id, "admin_not_owner"))
        await state.clear()
        return

    text = message.text.strip()
    try:
        target_id = int(text)
    except ValueError:
        await message.answer(get_text(user_id, "admin_add_manager_invalid_id"))
        return

    set_role(target_id, ROLE_MANAGER)

    await state.clear()
    await message.answer(
        get_text(user_id, "admin_add_manager_success").format(user_id=target_id)
    )


@router.message(F.text == "Список менеджеров 📋")
async def admin_list_managers_cmd(message: Message):
    user_id = message.from_user.id

    if not is_owner(user_id):
        await message.answer(get_text(user_id, "admin_not_owner"))
        return

    rows = list_managers()
    if not rows:
        await message.answer(get_text(user_id, "admin_managers_list_empty"))
        return

    lines = [get_text(user_id, "admin_managers_list_title"), ""]
    for uid, role in rows:
        lines.append(f"- {uid}: {role}")

    await message.answer("\n".join(lines))


# ---------- поддержка (заглушка для менеджера) ----------


@router.message(F.text == "Поддержка 💬")
async def admin_support_info(message: Message):
    user_id = message.from_user.id

    if not is_manager(user_id) and not is_owner(user_id):
        await message.answer(get_text(user_id, "admin_no_rights"))
        return

    await message.answer(get_text(user_id, "admin_support_info"))
