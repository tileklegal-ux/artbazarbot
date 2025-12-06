from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from keyboards import language_keyboard, get_main_keyboard
from database import set_user_language
from openai_api import analyze_market, pick_niche, recommendations

from navigation import navigation_kb, go_back, go_main_menu
from limit import check_limit
from roles_db import get_role
from premium_db import has_active_premium, get_premium
from utils import get_text
from usage_db import get_today_usage, get_last_requests


router = Router()


# ---------------- FSM ----------------

class UserStates(StatesGroup):
    await_market = State()
    await_niche = State()
    await_reco = State()

    await_margin_purchase = State()
    await_margin_shipping = State()
    await_margin_marketing = State()
    await_margin_other = State()
    await_margin_fee = State()
    await_margin_price = State()


# ---------------- СТАРТ И ЯЗЫК ----------------

@router.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer("Выберите язык:", reply_markup=language_keyboard)


@router.message(F.text.in_(["Русский 🇷🇺", "Кыргызча 🇰🇬", "Қазақша 🇰🇿"]))
async def set_language_handler(message: Message, state: FSMContext):
    mapping = {
        "Русский 🇷🇺": "ru",
        "Кыргызча 🇰🇬": "kg",
        "Қазақша 🇰🇿": "kz",
    }

    lang = mapping[message.text]
    set_user_language(message.from_user.id, lang)

    uid = message.from_user.id

    await state.clear()
    await message.answer(get_text(uid, "lang_chosen"))
    await message.answer(get_text(uid, "welcome"), reply_markup=get_main_keyboard(get_role(uid)))


@router.message(F.text == "🌐 Сменить язык")
async def change_language(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Выберите язык:", reply_markup=language_keyboard)


# ---------------- АНАЛИЗ РЫНКА ----------------

@router.message(F.text == "Анализ рынка 📊")
async def ask_market(message: Message, state: FSMContext):
    uid = message.from_user.id
    await state.set_state(UserStates.await_market)
    await message.answer(get_text(uid, "ask_market"), reply_markup=navigation_kb)


@router.message(UserStates.await_market, F.text == "⬅️ Назад")
async def back_market(message: Message, state: FSMContext):
    await go_back(message, state)


@router.message(UserStates.await_market)
async def run_market(message: Message, state: FSMContext):
    uid = message.from_user.id
    ok, msg = check_limit(uid)

    if not ok:
        await message.answer(msg, parse_mode="Markdown")
        await state.clear()
        return

    await message.answer(get_text(uid, "thinking"))

    answer = await analyze_market(message.text, user_id=uid)
    await message.answer(answer)

    await state.clear()


# ---------------- ПОДБОР НИШИ ----------------

@router.message(F.text == "Подбор ниши 🧭")
async def ask_niche(message: Message, state: FSMContext):
    uid = message.from_user.id
    await state.set_state(UserStates.await_niche)
    await message.answer(get_text(uid, "ask_niche"), reply_markup=navigation_kb)


@router.message(UserStates.await_niche, F.text == "⬅️ Назад")
async def back_niche(message: Message, state: FSMContext):
    await go_back(message, state)


@router.message(UserStates.await_niche)
async def run_niche(message: Message, state: FSMContext):
    uid = message.from_user.id
    ok, msg = check_limit(uid)

    if not ok:
        await message.answer(msg, parse_mode="Markdown")
        await state.clear()
        return

    await message.answer(get_text(uid, "thinking"))

    answer = await pick_niche(message.text, user_id=uid)
    await message.answer(answer)

    await state.clear()


# ---------------- РЕКОМЕНДАЦИИ ----------------

@router.message(F.text == "Рекомендации ⚡")
async def ask_reco(message: Message, state: FSMContext):
    uid = message.from_user.id
    await state.set_state(UserStates.await_reco)
    await message.answer(get_text(uid, "ask_reco"), reply_markup=navigation_kb)


@router.message(UserStates.await_reco, F.text == "⬅️ Назад")
async def back_reco(message: Message, state: FSMContext):
    await go_back(message, state)


@router.message(UserStates.await_reco)
async def run_reco(message: Message, state: FSMContext):
    uid = message.from_user.id
    ok, msg = check_limit(uid)

    if not ok:
        await message.answer(msg, parse_mode="Markdown")
        await state.clear()
        return

    await message.answer(get_text(uid, "thinking"))

    answer = await recommendations(message.text, user_id=uid)
    await message.answer(answer)

    await state.clear()


# ---------------- КАЛЬКУЛЯТОР МАРЖИ (PRO) ----------------

def _parse_number(text: str):
    text = text.replace(",", ".").strip()
    try:
        return float(text)
    except ValueError:
        return None


@router.message(F.text == "Калькулятор маржи 💰")
async def margin_start(message: Message, state: FSMContext):
    uid = message.from_user.id
    await state.set_state(UserStates.await_margin_purchase)
    await message.answer(get_text(uid, "margin_start"), reply_markup=navigation_kb)
    await message.answer(get_text(uid, "margin_ask_purchase"))


@router.message(UserStates.await_margin_purchase, F.text == "⬅️ Назад")
@router.message(UserStates.await_margin_shipping, F.text == "⬅️ Назад")
@router.message(UserStates.await_margin_marketing, F.text == "⬅️ Назад")
@router.message(UserStates.await_margin_other, F.text == "⬅️ Назад")
@router.message(UserStates.await_margin_fee, F.text == "⬅️ Назад")
@router.message(UserStates.await_margin_price, F.text == "⬅️ Назад")
async def margin_back_any(message: Message, state: FSMContext):
    await go_back(message, state)


@router.message(UserStates.await_margin_purchase)
async def margin_purchase(message: Message, state: FSMContext):
    uid = message.from_user.id
    value = _parse_number(message.text)
    if value is None:
        await message.answer(get_text(uid, "margin_invalid_number"))
        return

    await state.update_data(purchase=value)
    await state.set_state(UserStates.await_margin_shipping)
    await message.answer(get_text(uid, "margin_ask_shipping"))


@router.message(UserStates.await_margin_shipping)
async def margin_shipping(message: Message, state: FSMContext):
    uid = message.from_user.id
    value = _parse_number(message.text)
    if value is None:
        await message.answer(get_text(uid, "margin_invalid_number"))
        return

    await state.update_data(shipping=value)
    await state.set_state(UserStates.await_margin_marketing)
    await message.answer(get_text(uid, "margin_ask_marketing"))


@router.message(UserStates.await_margin_marketing)
async def margin_marketing(message: Message, state: FSMContext):
    uid = message.from_user.id
    value = _parse_number(message.text)
    if value is None:
        await message.answer(get_text(uid, "margin_invalid_number"))
        return

    await state.update_data(marketing=value)
    await state.set_state(UserStates.await_margin_other)
    await message.answer(get_text(uid, "margin_ask_other"))


@router.message(UserStates.await_margin_other)
async def margin_other(message: Message, state: FSMContext):
    uid = message.from_user.id
    value = _parse_number(message.text)
    if value is None:
        await message.answer(get_text(uid, "margin_invalid_number"))
        return

    await state.update_data(other=value)
    await state.set_state(UserStates.await_margin_fee)
    await message.answer(get_text(uid, "margin_ask_fee"))


@router.message(UserStates.await_margin_fee)
async def margin_fee(message: Message, state: FSMContext):
    uid = message.from_user.id
    value = _parse_number(message.text)
    if value is None:
        await message.answer(get_text(uid, "margin_invalid_number"))
        return

    if value < 0 or value > 80:
        # защита от странных значений
        await message.answer(get_text(uid, "margin_invalid_number"))
        return

    await state.update_data(fee=value)
    await state.set_state(UserStates.await_margin_price)
    await message.answer(get_text(uid, "margin_ask_price"))


@router.message(UserStates.await_margin_price)
async def margin_price(message: Message, state: FSMContext):
    uid = message.from_user.id
    price = _parse_number(message.text)
    if price is None or price <= 0:
        await message.answer(get_text(uid, "margin_invalid_number"))
        return

    data = await state.get_data()
    purchase = data.get("purchase", 0.0)
    shipping = data.get("shipping", 0.0)
    marketing = data.get("marketing", 0.0)
    other = data.get("other", 0.0)
    fee_percent = data.get("fee", 0.0)

    # расчёты
    cost_no_fee = purchase + shipping + marketing + other
    fee_rate = fee_percent / 100.0
    commission = price * fee_rate
    total_cost = cost_no_fee + commission
    profit = price - total_cost

    margin_pct = (profit / price * 100.0) if price > 0 else 0.0
    roi_pct = (profit / total_cost * 100.0) if total_cost > 0 else 0.0

    # точка безубыточности (цена, при которой прибыль 0)
    if fee_rate < 1.0:
        breakeven_price = cost_no_fee / (1.0 - fee_rate)
    else:
        breakeven_price = 0.0

    # рекомендуемая цена для ~30% маржи
    target_margin = 0.30
    denom = 1.0 - target_margin - fee_rate
    if denom > 0:
        target_price = cost_no_fee / denom
    else:
        target_price = 0.0

    text = get_text(uid, "margin_result").format(
        cost_no_fee=cost_no_fee,
        fee_amount=commission,
        total_cost=total_cost,
        price=price,
        profit=profit,
        margin_pct=margin_pct,
        roi_pct=roi_pct,
        breakeven_price=breakeven_price,
        target_price=target_price,
    )

    await message.answer(text)
    await state.clear()


# ---------------- ПРЕМИУМ ----------------

@router.message(F.text == "Премиум 🚀")
async def premium_block(message: Message):
    uid = message.from_user.id

    if has_active_premium(uid):
        until_ts, tariff = get_premium(uid)
        date = datetime.fromtimestamp(until_ts).strftime("%d.%m.%Y") if until_ts else "—"
        await message.answer(get_text(uid, "premium_info_yes").format(date=date))
        return

    await message.answer(get_text(uid, "premium_info_no"), parse_mode="Markdown")


# ---------------- ЛИЧНЫЙ КАБИНЕТ ----------------

@router.message(F.text == "Личный кабинет 👤")
async def user_cabinet(message: Message):
    uid = message.from_user.id

    parts: list[str] = []

    parts.append(get_text(uid, "cabinet_title"))

    # статус премиума
    if has_active_premium(uid):
        until_ts, tariff = get_premium(uid)
        date = datetime.fromtimestamp(until_ts).strftime("%d.%m.%Y")

        days_left = (until_ts - int(datetime.now().timestamp())) // 86400
        parts.append(get_text(uid, "cabinet_tariff").format(tariff=tariff, date=date, days=days_left))
    else:
        parts.append(get_text(uid, "cabinet_status_free"))

    # лимиты
    today_used = get_today_usage(uid)
    left = 3 - today_used if today_used < 3 else 0
    parts.append(get_text(uid, "cabinet_usage_today").format(used=today_used, left=left))

    # история
    rows = get_last_requests(uid, limit=10)
    if rows:
        parts.append(get_text(uid, "cabinet_history_header"))
        for _id, date_str, ts in rows:
            dt = datetime.fromtimestamp(ts).strftime("%d.%m.%Y %H:%M")
            parts.append(f"• {dt}")
    else:
        parts.append(get_text(uid, "cabinet_history_empty"))

    text = "\n\n".join(parts)
    await message.answer(text)


# ---------------- ГЛАВНОЕ МЕНЮ ----------------

@router.message(F.text == "🏠 Главное меню")
async def main_menu(message: Message):
    await go_main_menu(message)


# ---------------- ФОЛЛБЭК ----------------

@router.message()
async def fallback(message: Message):
    uid = message.from_user.id
    await message.answer(get_text(uid, "unknown"), reply_markup=get_main_keyboard(get_role(uid)))
