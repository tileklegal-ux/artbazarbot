from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from keyboards import language_keyboard, get_main_keyboard
from database import set_user_language, upsert_user
from openai_api import analyze_market, pick_niche, recommendations
from roles_db import get_role
from premium_db import has_active_premium, get_premium
from limit import check_limit
from utils import get_text

router = Router()


class UserStates(StatesGroup):
    await_market = State()
    await_niche = State()
    await_reco = State()


# ---------- /start ----------
@router.message(F.text == "/start")
async def cmd_start(message: Message):
    user = message.from_user
    # Обновляем/создаём пользователя в БД
    upsert_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
    )

    await message.answer(
        get_text(user.id, "choose_language"),
        reply_markup=language_keyboard,
    )


# ---------- Установка языка ----------
@router.message(F.text == "Русский 🇷🇺")
async def set_lang_ru(message: Message):
    await _set_language_and_show_menu(message, "ru")


@router.message(F.text == "Кыргызча 🇰🇬")
async def set_lang_kg(message: Message):
    await _set_language_and_show_menu(message, "kg")


@router.message(F.text == "Қазақша 🇰🇿")
async def set_lang_kz(message: Message):
    await _set_language_and_show_menu(message, "kz")


async def _set_language_and_show_menu(message: Message, lang: str):
    user_id = message.from_user.id
    set_user_language(user_id, lang)
    role = get_role(user_id)
    kb = get_main_keyboard(role)

    await message.answer(get_text(user_id, "lang_chosen"))
    await message.answer(get_text(user_id, "welcome"), reply_markup=kb)


# ---------- Анализ рынка ----------
@router.message(F.text == "Анализ рынка 📊")
async def ask_market_question(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await state.set_state(UserStates.await_market)
    await message.answer(get_text(user_id, "ask_market"))


@router.message(UserStates.await_market)
async def handle_market_question(message: Message, state: FSMContext):
    user_id = message.from_user.id

    ok, msg = check_limit(user_id)
    if not ok:
        await message.answer(msg, parse_mode="Markdown")
        await state.clear()
        return

    await message.answer(get_text(user_id, "thinking"))

    try:
        answer = await analyze_market(message.text, user_id=user_id)
    except Exception:
        await message.answer(get_text(user_id, "error_ai"))
        await state.clear()
        return

    await message.answer(answer)
    await state.clear()


# ---------- Подбор ниши ----------
@router.message(F.text == "Подбор ниши 🧭")
async def ask_niche_question(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await state.set_state(UserStates.await_niche)
    await message.answer(get_text(user_id, "ask_niche"))


@router.message(UserStates.await_niche)
async def handle_niche_question(message: Message, state: FSMContext):
    user_id = message.from_user.id

    ok, msg = check_limit(user_id)
    if not ok:
        await message.answer(msg, parse_mode="Markdown")
        await state.clear()
        return

    await message.answer(get_text(user_id, "thinking"))

    try:
        answer = await pick_niche(message.text, user_id=user_id)
    except Exception:
        await message.answer(get_text(user_id, "error_ai"))
        await state.clear()
        return

    await message.answer(answer)
    await state.clear()


# ---------- Рекомендации ----------
@router.message(F.text == "Рекомендации ⚡")
async def ask_reco_question(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await state.set_state(UserStates.await_reco)
    await message.answer(get_text(user_id, "ask_reco"))


@router.message(UserStates.await_reco)
async def handle_reco_question(message: Message, state: FSMContext):
    user_id = message.from_user.id

    ok, msg = check_limit(user_id)
    if not ok:
        await message.answer(msg, parse_mode="Markdown")
        await state.clear()
        return

    await message.answer(get_text(user_id, "thinking"))

    try:
        answer = await recommendations(message.text, user_id=user_id)
    except Exception:
        await message.answer(get_text(user_id, "error_ai"))
        await state.clear()
        return

    await message.answer(answer)
    await state.clear()


# ---------- Калькулятор маржи (пока заглушка) ----------
@router.message(F.text == "Калькулятор маржи 💰")
async def margin_stub(message: Message):
    user_id = message.from_user.id
    await message.answer(get_text(user_id, "margin_soon"))


# ---------- Премиум ----------
@router.message(F.text == "Премиум 🚀")
async def premium_info(message: Message):
    uid = message.from_user.id

    if has_active_premium(uid):
        data = get_premium(uid)
        if data:
            until_ts, tariff = data
            dt_str = datetime.fromtimestamp(until_ts).strftime("%d.%m.%Y")
            text = get_text(uid, "premium_info_yes").format(date=dt_str)
            if tariff:
                text += f"\n\nТариф: *{tariff}*"
        else:
            text = "У тебя активный премиум-доступ. Пользуйся без ограничений 🚀"

        await message.answer(text, parse_mode="Markdown")
        return

    await message.answer(get_text(uid, "premium_info_no"), parse_mode="Markdown")


# ---------- Фоллбэк ----------
@router.message()
async def fallback(message: Message):
    user_id = message.from_user.id
    role = get_role(user_id)
    kb = get_main_keyboard(role)
    await message.answer(get_text(user_id, "unknown"), reply_markup=kb)
