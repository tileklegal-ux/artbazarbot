from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from keyboards import language_keyboard, get_main_keyboard
from database import set_user_language, get_user_language
from openai_api import analyze_market, pick_niche, recommendations

from navigation import navigation_kb, go_back, go_main_menu
from limit import check_limit
from roles_db import get_role
from premium_db import has_active_premium, get_premium


router = Router()


# ---------------- FSM ----------------

class UserStates(StatesGroup):
    await_market = State()
    await_niche = State()
    await_reco = State()


# ---------------- Тексты ----------------

def get_texts(user_id: int):
    lang = get_user_language(user_id) or "ru"

    if lang == "kg":
        return {
            "lang_chosen": "Тилди сактап койдум.",
            "welcome": "ArtBazar AI'га кош келиңиз!",
            "ask_market": "Кайсы товар боюнча рынокту текшеребиз?",
            "ask_niche": "Кайсы нишаны караганы жатасыз?",
            "ask_reco": "Сатуулар боюнча кеңеш керекпи? Товарыңды жаз:",
            "thinking": "Жооп даярдап жатам…",
            "margin_soon": "Маржа калькулятору жакында.",
            "premium_info_no": "Премиум активдүү эмес. 3 суроо лимит.",
            "premium_info_yes": "Премиум активдүү: {date} чейин.",
            "unknown": "Түшүнгөн жокмун. Менюдан тандаңыз."
        }

    if lang == "kz":
        return {
            "lang_chosen": "Тілді сақтап қойдым.",
            "welcome": "ArtBazar AI — онлайн сатушыларға ассистент!",
            "ask_market": "Қандай тауар бойынша нарықты талдаймыз?",
            "ask_niche": "Қандай нишаны ойлап жүрсіз?",
            "ask_reco": "Сатылым кеңесі үшін тауарды жазыңыз:",
            "thinking": "Жауап дайындап жатырмын…",
            "margin_soon": "Маржа калькуляторы жақында.",
            "premium_info_no": "Премиум белсендірілмеген.",
            "premium_info_yes": "Премиум белсенді: {date} дейін.",
            "unknown": "Түсінбедім. Менюді пайдаланыңыз."
        }

    return {
        "lang_chosen": "Я запомнил язык.",
        "welcome": "Добро пожаловать в ArtBazar AI!",
        "ask_market": "Опиши товар или нишу для анализа:",
        "ask_niche": "Что хочешь анализировать? Опиши нишу:",
        "ask_reco": "Опиши товар — дам рекомендации:",
        "thinking": "Думаю над ответом…",
        "margin_soon": "Калькулятор маржи скоро.",
        "premium_info_no": "Премиум не активирован. Лимит — 3 запроса.",
        "premium_info_yes": "Премиум активен до {date}.",
        "unknown": "Команда не распознана."
    }


# ---------------- СТАРТ ----------------

@router.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer("Выберите язык:", reply_markup=language_keyboard)


@router.message(F.text.in_(["Русский 🇷🇺", "Кыргызча 🇰🇬", "Қазақша 🇰🇿"]))
async def set_language(message: Message):
    mapping = {
        "Русский 🇷🇺": "ru",
        "Кыргызча 🇰🇬": "kg",
        "Қазақша 🇰🇿": "kz",
    }

    lang = mapping[message.text]
    set_user_language(message.from_user.id, lang)

    t = get_texts(message.from_user.id)
    role = get_role(message.from_user.id)

    await message.answer(t["lang_chosen"])
    await message.answer(t["welcome"], reply_markup=get_main_keyboard(role))


# ---------------- АНАЛИЗ РЫНКА ----------------

@router.message(F.text == "Анализ рынка 📊")
async def ask_market(message: Message, state: FSMContext):
    t = get_texts(message.from_user.id)
    await state.set_state(UserStates.await_market)
    await message.answer(t["ask_market"], reply_markup=navigation_kb)


@router.message(UserStates.await_market, F.text == "⬅️ Назад")
async def back_market(message: Message, state: FSMContext):
    await go_back(message, state)


@router.message(UserStates.await_market)
async def run_market(message: Message, state: FSMContext):
    ok, msg = check_limit(message.from_user.id)
    if not ok:
        await message.answer(msg, parse_mode="Markdown")
        await state.clear()
        return

    t = get_texts(message.from_user.id)
    await message.answer(t["thinking"])

    answer = await analyze_market(message.text, user_id=message.from_user.id)
    await message.answer(answer)

    await state.clear()


# ---------------- ПОДБОР НИШИ ----------------

@router.message(F.text == "Подбор ниши 🧭")
async def ask_niche(message: Message, state: FSMContext):
    t = get_texts(message.from_user.id)
    await state.set_state(UserStates.await_niche)
    await message.answer(t["ask_niche"], reply_markup=navigation_kb)


@router.message(UserStates.await_niche, F.text == "⬅️ Назад")
async def back_niche(message: Message, state: FSMContext):
    await go_back(message, state)


@router.message(UserStates.await_niche)
async def run_niche(message: Message, state: FSMContext):
    ok, msg = check_limit(message.from_user.id)
    if not ok:
        await message.answer(msg, parse_mode="Markdown")
        await state.clear()
        return

    t = get_texts(message.from_user.id)
    await message.answer(t["thinking"])

    answer = await pick_niche(message.text, user_id=message.from_user.id)
    await message.answer(answer)

    await state.clear()


# ---------------- РЕКОМЕНДАЦИИ ----------------

@router.message(F.text == "Рекомендации ⚡")
async def ask_reco(message: Message, state: FSMContext):
    t = get_texts(message.from_user.id)
    await state.set_state(UserStates.await_reco)
    await message.answer(t["ask_reco"], reply_markup=navigation_kb)


@router.message(UserStates.await_reco, F.text == "⬅️ Назад")
async def back_reco(message: Message, state: FSMContext):
    await go_back(message, state)


@router.message(UserStates.await_reco)
async def run_reco(message: Message, state: FSMContext):
    ok, msg = check_limit(message.from_user.id)
    if not ok:
        await message.answer(msg, parse_mode="Markdown")
        await state.clear()
        return

    t = get_texts(message.from_user.id)
    await message.answer(t["thinking"])

    answer = await recommendations(message.text, user_id=message.from_user.id)
    await message.answer(answer)

    await state.clear()


# ---------------- ПРЕМИУМ ----------------

@router.message(F.text == "Премиум 🚀")
async def premium_block(message: Message):
    uid = message.from_user.id
    t = get_texts(uid)

    if has_active_premium(uid):
        until_ts, tariff = get_premium(uid)
        date = datetime.fromtimestamp(until_ts).strftime("%d.%m.%Y")
        await message.answer(t["premium_info_yes"].format(date=date))
        return

    await message.answer(t["premium_info_no"])


# ---------------- ГЛАВНОЕ МЕНЮ ----------------

@router.message(F.text == "🏠 Главное меню")
async def main_menu(message: Message):
    await go_main_menu(message)


# ---------------- ФОЛЛБЭК ----------------

@router.message()
async def fallback(message: Message):
    t = get_texts(message.from_user.id)
    role = get_role(message.from_user.id)
    await message.answer(t["unknown"], reply_markup=get_main_keyboard(role))
