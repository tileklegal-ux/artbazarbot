from datetime import datetime
from typing import Optional

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from keyboards import language_keyboard, get_main_keyboard
from database import set_user_language, upsert_user
from openai_api import analyze_market, pick_niche, recommendations
from roles_db import get_role
from premium_db import has_active_premium, get_premium
from limit import check_limit, DAILY_LIMIT
from utils import get_text
from usage_db import get_today_usage, get_recent_usage

router = Router()


class UserStates(StatesGroup):
    # AI-флоу
    await_market = State()
    await_niche = State()
    await_reco = State()

    # Маржа калькулятор
    margin_purchase = State()
    margin_delivery = State()
    margin_marketing = State()
    margin_other = State()
    margin_fee = State()
    margin_price = State()


# ---------- /start ----------
@router.message(F.text == "/start")
async def cmd_start(message: Message):
    user = message.from_user
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


# ---------- Смена языка по кнопке ----------
@router.message(F.text == "🌐 Сменить язык")
async def change_language(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        get_text(message.from_user.id, "choose_language"),
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


# ---------- Калькулятор маржи (FSM) ----------
def _parse_number(text: str) -> Optional[float]:
    text = text.replace(",", ".").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


@router.message(F.text == "Калькулятор маржи 💰")
async def margin_start(message: Message, state: FSMContext):
    user_id = message.from_user.id

    # считаем как отдельный запрос → учитываем лимит
    ok, msg = check_limit(user_id)
    if not ok:
        await message.answer(msg, parse_mode="Markdown")
        return

    await state.set_state(UserStates.margin_purchase)
    await message.answer(
        get_text(user_id, "margin_ask_purchase"),
        parse_mode="Markdown",
    )


@router.message(UserStates.margin_purchase)
async def margin_step_purchase(message: Message, state: FSMContext):
    user_id = message.from_user.id
    value = _parse_number(message.text)
    if value is None:
        await message.answer(get_text(user_id, "margin_invalid_number"))
        return

    await state.update_data(purchase=value)
    await state.set_state(UserStates.margin_delivery)
    await message.answer(
        get_text(user_id, "margin_ask_delivery"),
        parse_mode="Markdown",
    )


@router.message(UserStates.margin_delivery)
async def margin_step_delivery(message: Message, state: FSMContext):
    user_id = message.from_user.id
    value = _parse_number(message.text)
    if value is None:
        await message.answer(get_text(user_id, "margin_invalid_number"))
        return

    await state.update_data(delivery=value)
    await state.set_state(UserStates.margin_marketing)
    await message.answer(
        get_text(user_id, "margin_ask_marketing"),
        parse_mode="Markdown",
    )


@router.message(UserStates.margin_marketing)
async def margin_step_marketing(message: Message, state: FSMContext):
    user_id = message.from_user.id
    value = _parse_number(message.text)
    if value is None:
        await message.answer(get_text(user_id, "margin_invalid_number"))
        return

    await state.update_data(marketing=value)
    await state.set_state(UserStates.margin_other)
    await message.answer(
        get_text(user_id, "margin_ask_other"),
        parse_mode="Markdown",
    )


@router.message(UserStates.margin_other)
async def margin_step_other(message: Message, state: FSMContext):
    user_id = message.from_user.id
    value = _parse_number(message.text)
    if value is None:
        await message.answer(get_text(user_id, "margin_invalid_number"))
        return

    await state.update_data(other=value)
    await state.set_state(UserStates.margin_fee)
    await message.answer(
        get_text(user_id, "margin_ask_fee"),
        parse_mode="Markdown",
    )


@router.message(UserStates.margin_fee)
async def margin_step_fee(message: Message, state: FSMContext):
    user_id = message.from_user.id
    value = _parse_number(message.text)
    if value is None:
        await message.answer(get_text(user_id, "margin_invalid_number"))
        return

    # value — в процентах (0..100)
    await state.update_data(fee=value)
    await state.set_state(UserStates.margin_price)
    await message.answer(
        get_text(user_id, "margin_ask_price"),
        parse_mode="Markdown",
    )


@router.message(UserStates.margin_price)
async def margin_step_price(message: Message, state: FSMContext):
    user_id = message.from_user.id
    sale_price = _parse_number(message.text)
    if sale_price is None or sale_price <= 0:
        await message.answer(get_text(user_id, "margin_invalid_number"))
        return

    data = await state.get_data()
    purchase = float(data.get("purchase", 0.0))
    delivery = float(data.get("delivery", 0.0))
    marketing = float(data.get("marketing", 0.0))
    other = float(data.get("other", 0.0))
    fee_percent = float(data.get("fee", 0.0))

    fee_rate = max(0.0, fee_percent / 100.0)

    cost_base = purchase + delivery + marketing + other
    fee_amount = sale_price * fee_rate
    total_cost = cost_base + fee_amount
    profit = sale_price - total_cost

    if sale_price > 0:
        margin_percent = (profit / sale_price) * 100.0
    else:
        margin_percent = 0.0

    if total_cost > 0:
        roi_percent = (profit / total_cost) * 100.0
    else:
        roi_percent = 0.0

    # Точка безубыточности
    breakeven_price = None
    if 0.0 <= fee_rate < 1.0:
        denominator = 1.0 - fee_rate
        if denominator > 0:
            breakeven_price = cost_base / denominator

    # Цена для ~30% маржи
    recommended_price = None
    if 0.0 <= fee_rate < 1.0:
        denominator = (1.0 - fee_rate) - 0.30
        if denominator > 0:
            recommended_price = cost_base / denominator

    # Формируем дополнительные блоки
    breakeven_block = ""
    recommended_block = ""
    if breakeven_price is not None:
        breakeven_block = get_text(user_id, "margin_breakeven_line").format(
            breakeven=breakeven_price
        )
    if recommended_price is not None:
        recommended_block = get_text(user_id, "margin_recommended_line").format(
            recommended=recommended_price
        )

    template = get_text(user_id, "margin_result")
    text = template.format(
        cost_base=cost_base,
        fee_amount=fee_amount,
        total_cost=total_cost,
        sale_price=sale_price,
        profit=profit,
        margin_percent=margin_percent,
        roi_percent=roi_percent,
        breakeven_block=breakeven_block,
        recommended_block=recommended_block,
    )

    await message.answer(text, parse_mode="Markdown")
    await state.clear()


# ---------- Премиум ----------
@router.message(F.text == "Премиум 🚀")
async def premium_info(message: Message):
    uid = message.from_user.id

    if has_active_premium(uid):
        data = get_premium(uid)
        if data:
            until_ts, tariff = data
            dt_str = datetime.fromtimestamp(until_ts).strftime("%d.%m.%Y")
            now_ts = datetime.now().timestamp()
            days_left = max(0, int((until_ts - now_ts) // 86400))

            base_text = get_text(uid, "premium_info_yes").format(date=dt_str)
            extra = get_text(uid, "cabinet_premium_until").format(
                date=dt_str, days=days_left
            )
            text = base_text + "\n\n" + extra

            if tariff:
                text += "\n" + get_text(uid, "cabinet_tariff_label").format(
                    tariff=tariff
                )
        else:
            text = get_text(uid, "premium_info_yes").format(date="—")

        await message.answer(text, parse_mode="Markdown")
        return

    await message.answer(get_text(uid, "premium_info_no"), parse_mode="Markdown")


# ---------- Личный кабинет ----------
@router.message(F.text == "Личный кабинет 👤")
async def personal_cabinet(message: Message):
    uid = message.from_user.id

    used_today = get_today_usage(uid)
    has_prem = has_active_premium(uid)

    lines = [get_text(uid, "cabinet_title"), ""]

    if has_prem:
        lines.append(get_text(uid, "cabinet_premium"))
        data = get_premium(uid)
        if data:
            until_ts, tariff = data
            dt_str = datetime.fromtimestamp(until_ts).strftime("%d.%m.%Y")
            now_ts = datetime.now().timestamp()
            days_left = max(0, int((until_ts - now_ts) // 86400))

            lines.append(
                get_text(uid, "cabinet_premium_until").format(
                    date=dt_str, days=days_left
                )
            )
            if tariff:
                lines.append(
                    get_text(uid, "cabinet_tariff_label").format(tariff=tariff)
                )
        lines.append("")
    else:
        lines.append(get_text(uid, "cabinet_basic"))
        lines.append("")

    # Лимиты
    lines.append(get_text(uid, "cabinet_limits_title"))
    if has_prem:
        lines.append(
            get_text(uid, "cabinet_limits_premium").format(
                used=used_today,
            )
        )
    else:
        left = max(0, DAILY_LIMIT - used_today)
        lines.append(
            get_text(uid, "cabinet_limits_basic").format(
                used=used_today,
                limit=DAILY_LIMIT,
                left=left,
            )
        )

    # История usage
    history = get_recent_usage(uid, limit=5)
    lines.append("")
    if not history:
        lines.append(get_text(uid, "cabinet_history_empty"))
    else:
        lines.append(get_text(uid, "cabinet_history_title"))
        for action, ts in history:
            dt_str = datetime.fromtimestamp(ts).strftime("%d.%m.%Y %H:%M")
            # без текста действия, по ТЗ достаточно даты/времени
            lines.append(f"- {dt_str}")

    text = "\n".join(lines)
    await message.answer(text)


# ---------- Фоллбэк ----------
@router.message()
async def fallback(message: Message):
    user_id = message.from_user.id
    role = get_role(user_id)
    kb = get_main_keyboard(role)
    await message.answer(get_text(user_id, "unknown"), reply_markup=kb)
