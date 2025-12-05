from aiogram import Router, F
from aiogram.types import Message

from roles import is_owner, is_manager, MANAGERS
from admin_keyboards import owner_keyboard, manager_keyboard
from database import set_user_language  # позже расширим
from premium_db import give_premium, remove_premium  # создадим файл premium_db.py

router_admin = Router()


# ---------- Команда входа в админку ----------
@router_admin.message(F.text == "Админ панель")
async def admin_entry(message: Message):
    user_id = message.from_user.id

    if is_owner(user_id):
        await message.answer("Панель владельца открыта:", reply_markup=owner_keyboard)

    elif is_manager(user_id):
        await message.answer("Панель менеджера открыта:", reply_markup=manager_keyboard)

    else:
        await message.answer("У вас нет доступа к административной панели.")


# ---------- Управление менеджерами ----------
@router_admin.message(F.text == "Управление менеджерами")
async def manage_managers(message: Message):
    if not is_owner(message.from_user.id):
        return await message.answer("Только владелец может управлять менеджерами.")

    await message.answer(
        "Отправь ID менеджера с командой:\n"
        "/add_manager 123456\n"
        "/remove_manager 123456"
    )


@router_admin.message(F.text.startswith("/add_manager"))
async def add_manager(message: Message):
    if not is_owner(message.from_user.id):
        return

    try:
        new_id = int(message.text.split()[1])
        MANAGERS.add(new_id)
        await message.answer(f"Менеджер {new_id} добавлен.")
    except:
        await message.answer("Неверный формат. Используй: /add_manager ID")


@router_admin.message(F.text.startswith("/remove_manager"))
async def remove_manager(message: Message):
    if not is_owner(message.from_user.id):
        return

    try:
        delete_id = int(message.text.split()[1])
        MANAGERS.discard(delete_id)
        await message.answer(f"Менеджер {delete_id} удалён.")
    except:
        await message.answer("Неверный формат. Используй: /remove_manager ID")


# ---------- Управление премиум-доступом ----------
@router_admin.message(F.text == "Премиум-доступы")
async def premium_access(message: Message):
    if not is_manager(message.from_user.id):
        return await message.answer("Нет доступа.")

    await message.answer(
        "Доступные команды:\n"
        "/give_premium ID 30\n"
        "/remove_premium ID"
    )


@router_admin.message(F.text.startswith("/give_premium"))
async def give_p(message: Message):
    if not is_manager(message.from_user.id):
        return

    try:
        _, user_id, days = message.text.split()
        give_premium(int(user_id), int(days))
        await message.answer(f"Премиум выдан: {user_id} на {days} дней.")
    except:
        await message.answer("Формат: /give_premium ID DAYS")


@router_admin.message(F.text.startswith("/remove_premium"))
async def remove_p(message: Message):
    if not is_manager(message.from_user.id):
        return

    try:
        _, user_id = message.text.split()
        remove_premium(int(user_id))
        await message.answer(f"Премиум снят у: {user_id}")
    except:
        await message.answer("Формат: /remove_premium ID")
