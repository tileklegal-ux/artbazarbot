from aiogram import Router, F
from aiogram.types import Message

from admin_keyboards import owner_admin_kb, manager_admin_kb
from keyboards import get_main_keyboard
from roles_db import is_owner, is_manager, set_role, list_managers, get_role, ROLE_MANAGER
from premium_db import has_active_premium, get_premium, set_premium

router = Router()


# ---------- вход в панели ----------

@router.message(F.text == "Админ 👑")
async def enter_owner_panel(message: Message):
    if not is_owner(message.from_user.id):
        await message.answer("У тебя нет прав владельца.")
        return

    await message.answer(
        "👑 Панель владельца. Здесь можно управлять менеджерами и премиум-доступом.",
        reply_markup=owner_admin_kb,
    )


@router.message(F.text == "Менеджер 📋")
async def enter_manager_panel(message: Message):
    if not is_manager(message.from_user.id):
        await message.answer("Доступно только менеджерам и владельцу.")
        return

    await message.answer(
        "📋 Панель менеджера. Работа с премиум-клиентами и поддержкой.",
        reply_markup=manager_admin_kb,
    )


# ---------- возврат в главное меню ----------

@router.message(F.text == "⬅️ В главное меню")
async def back_to_main(message: Message):
    from roles_db import get_role  # локальный импорт, чтобы избежать циклов

    role = get_role(message.from_user.id)
    kb = get_main_keyboard(role)
    await message.answer("Возвращаю основное меню.", reply_markup=kb)


# ---------- премиум: выдача (упрощённо через reply) ----------

@router.message(F.text == "Выдать премиум 🎁")
async def stub_give_premium(message: Message):
    """
    Пока делаем заглушку: объясняем, как выдать премиум вручную.
    Реальную FSM для ввода ID и тарифа можно докрутить позже.
    """
    await message.answer(
        "Пока выдача премиума делается вручную через команду:\n\n"
        "/gift_premium user_id days тариф\n\n"
        "Пример: /gift_premium 123456789 30 '1 месяц'."
    )


@router.message(F.text == "Список премиум 👥")
async def list_premium_stub(message: Message):
    await message.answer(
        "Список премиум-клиентов пока не выведен в интерфейс.\n"
        "Позже сделаем отдельный экран со списком."
    )


# ---------- команды, которыми реально можно пользоваться уже сейчас ----------

@router.message(F.text.startswith("/gift_premium"))
async def cmd_gift_premium(message: Message):
    """
    /gift_premium user_id days тариф
    Доступно только владельцу.
    """
    if not is_owner(message.from_user.id):
        await message.answer("Только владелец может дарить премиум этой командой.")
        return

    parts = message.text.split(maxsplit=3)
    if len(parts) < 4:
        await message.answer(
            "Формат: /gift_premium user_id days тариф\n"
            "Пример: /gift_premium 123456789 30 1_месяц"
        )
        return

    try:
        target_id = int(parts[1])
        days = int(parts[2])
        tariff = parts[3]
    except ValueError:
        await message.answer("user_id и days должны быть числами.")
        return

    set_premium(target_id, days, tariff)
    await message.answer(
        f"Премиум на {days} дней ({tariff}) выдан пользователю {target_id}."
    )


# ---------- управление менеджерами (через команды) ----------

@router.message(F.text == "Добавить менеджера ➕")
async def hint_add_manager(message: Message):
    if not is_owner(message.from_user.id):
        await message.answer("Только владелец может назначать менеджеров.")
        return

    await message.answer(
        "Чтобы назначить менеджера, используй команду:\n\n"
        "/add_manager user_id\n\n"
        "Позже сделаем это через кнопки."
    )


@router.message(F.text == "Список менеджеров 📋")
async def show_managers(message: Message):
    if not is_owner(message.from_user.id):
        await message.answer("Только владелец может смотреть список менеджеров.")
        return

    managers = list_managers()
    if not managers:
        await message.answer("Пока нет менеджеров.")
        return

    lines = []
    for uid, role in managers:
        lines.append(f"{uid} — {role}")
    await message.answer("Менеджеры и владельцы:\n" + "\n".join(lines))


@router.message(F.text.startswith("/add_manager"))
async def cmd_add_manager(message: Message):
    if not is_owner(message.from_user.id):
        await message.answer("Только владелец может назначать менеджеров.")
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Формат: /add_manager user_id")
        return

    try:
        target_id = int(parts[1])
    except ValueError:
        await message.answer("user_id должен быть числом.")
        return

    set_role(target_id, ROLE_MANAGER)
    await message.answer(f"Пользователь {target_id} назначен менеджером.")
