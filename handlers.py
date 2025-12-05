from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Импорт из ОДНОГО файла messages.py
from messages import get_main_keyboard, get_text, MENU_TEXTS, LANG_NAMES
# Импорт из других файлов
from db import get_user_language, set_user_language
from ai_services import get_ai_analysis, get_niche_analysis, get_recommendations
from utils import calculate_margin, format_margin_report

import logging

router = Router()

# === МАШИНА СОСТОЯНИЙ (FSM) ===
class BotStates(StatesGroup):
    """Определяет все возможные состояния бота для обработки ввода пользователя."""
    
    # 1. Анализ
    waiting_for_product = State()
    waiting_for_niche = State()
    waiting_for_recom = State()
    
    # 2. Калькулятор
    calc_cost = State()
    calc_delivery = State()
    calc_marketing = State()
    calc_price = State()
    calc_extra = State()

# === ХЕЛПЕРЫ ===

async def get_current_lang(user_id):
    """Получает код языка пользователя из БД, по умолчанию 'ru'."""
    return await get_user_language(user_id)

async def send_menu(message: types.Message, lang: str, text_key: str = "menu", state: FSMContext = None):
    """Отправляет главное меню и очищает состояние, если оно активно."""
    if state:
        await state.clear()
    
    await message.answer(
        get_text(lang, text_key),
        reply_markup=get_main_keyboard(lang)
    )

# === 1. СТАРТ И ВЫБОР ЯЗЫКА ===

@router.message(Command("start"))
async def start_cmd(message: types.Message, state: FSMContext):
    """Обработка команды /start."""
    await state.clear()
    
    # Клавиатура выбора языка (Inline)
    kb = [
        [types.InlineKeyboardButton(text=LANG_NAMES["ru"], callback_data="lang_ru")],
        [types.InlineKeyboardButton(text=LANG_NAMES["kz"], callback_data="lang_kz")],
        [types.InlineKeyboardButton(text=LANG_NAMES["kg"], callback_data="lang_kg")]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
    
    # Отправляем приветствие на русском по умолчанию для выбора
    await message.answer(get_text("ru", "start"), reply_markup=keyboard)

@router.callback_query(F.data.startswith("lang_"))
async def lang_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора языка через Inline кнопку."""
    lang_code = callback.data.split("_")[1]
    user_id = callback.from_user.id
    
    # 1. Сохраняем язык в БД
    await set_user_language(user_id, lang_code)
    
    # 2. Отправляем меню
    await callback.message.delete()
    await send_menu(callback.message, lang_code, text_key="lang_set", state=state)
    await callback.answer() # Закрываем уведомление

# === 2. ГЛАВНОЕ МЕНЮ И КНОПКА "НАЗАД" ===

# Хэндлер для кнопки "Назад / Меню"
@router.message(lambda msg: any(msg.text == texts["btn_back"] for texts in MENU_TEXTS.values()))
@router.message(F.text.in_(["/menu", "/main"])) # Дополнительные команды для меню
async def back_to_menu(message: types.Message, state: FSMContext):
    lang = await get_current_lang(message.from_user.id)
    await send_menu(message, lang, text_key="menu_back", state=state)

# === 3. РОУТИНГ ПО КНОПКАМ МЕНЮ ===

@router.message(lambda msg: any(msg.text == texts["btn_analysis"] for texts in MENU_TEXTS.values()))
async def menu_analysis(message: types.Message, state: FSMContext):
    lang = await get_current_lang(message.from_user.id)
    await state.set_state(BotStates.waiting_for_product)
    await message.answer(get_text(lang, "enter_product"))

@router.message(lambda msg: any(msg.text == texts["btn_niche"] for texts in MENU_TEXTS.values()))
async def menu_niche(message: types.Message, state: FSMContext):
    lang = await get_current_lang(message.from_user.id)
    await state.set_state(BotStates.waiting_for_niche)
    await message.answer(get_text(lang, "enter_niche"))

@router.message(lambda msg: any(msg.text == texts["btn_recom"] for texts in MENU_TEXTS.values()))
async def menu_recom(message: types.Message, state: FSMContext):
    lang = await get_current_lang(message.from_user.id)
    await state.set_state(BotStates.waiting_for_recom)
    await message.answer(get_text(lang, "enter_recom"))

@router.message(lambda msg: any(msg.text == texts["btn_premium"] for texts in MENU_TEXTS.values()))
async def menu_premium(message: types.Message):
    lang = await get_current_lang(message.from_user.id)
    await message.answer(get_text(lang, "premium"))


# === 4. ОБРАБОТКА AI ЗАПРОСОВ (ФУНКЦИОНАЛЬНЫЕ КНОПКИ) ===

@router.message(BotStates.waiting_for_product)
async def process_product_analysis(message: types.Message, state: FSMContext):
    lang = await get_current_lang(message.from_user.id)
    await message.answer(get_text(lang, "processing"))
    
    # Вызов AI
    response = await get_ai_analysis(message.text, lang)
    
    await message.answer(response, parse_mode="Markdown", reply_markup=get_main_keyboard(lang))
    await state.clear()

@router.message(BotStates.waiting_for_niche)
async def process_niche_analysis(message: types.Message, state: FSMContext):
    lang = await get_current_lang(message.from_user.id)
    await message.answer(get_text(lang, "processing"))
    
    response = await get_niche_analysis(message.text, lang)
    
    await message.answer(response, parse_mode="Markdown", reply_markup=get_main_keyboard(lang))
    await state.clear()

@router.message(BotStates.waiting_for_recom)
async def process_recommendations(message: types.Message, state: FSMContext):
    lang = await get_current_lang(message.from_user.id)
    await message.answer(get_text(lang, "processing"))
    
    response = await get_recommendations(message.text, lang)
    
    await message.answer(response, parse_mode="Markdown", reply_markup=get_main_keyboard(lang))
    await state.clear()


# === 5. КАЛЬКУЛЯТОР МАРЖИ (ЦЕПОЧКА ШАГОВ FSM) ===

@router.message(lambda msg: any(msg.text == texts["btn_calc"] for texts in MENU_TEXTS.values()))
async def menu_calc(message: types.Message, state: FSMContext):
    lang = await get_current_lang(message.from_user.id)
    await state.set_state(BotStates.calc_cost)
    await message.answer(get_text(lang, "calc_start"))

# Хелпер для проверки чисел
async def validate_number(message: types.Message, state: FSMContext, next_state: State, key: str, next_msg_key: str):
    lang = await get_current_lang(message.from_user.id)
    try:
        # Заменяем запятую на точку для правильной конвертации в float
        value = float(message.text.replace(',', '.')) 
        
        if value < 0: raise ValueError
        
        await state.update_data({key: value})
        await state.set_state(next_state)
        await message.answer(get_text(lang, next_msg_key))
    except ValueError:
        await message.answer(get_text(lang, "calc_error"))

@router.message(BotStates.calc_cost)
async def step_cost(message: types.Message, state: FSMContext):
    await validate_number(message, state, BotStates.calc_delivery, "cost", "calc_delivery")

@router.message(BotStates.calc_delivery)
async def step_delivery(message: types.Message, state: FSMContext):
    await validate_number(message, state, BotStates.calc_marketing, "delivery", "calc_marketing")

@router.message(BotStates.calc_marketing)
async def step_marketing(message: types.Message, state: FSMContext):
    await validate_number(message, state, BotStates.calc_price, "marketing", "calc_price")

@router.message(BotStates.calc_price)
async def step_price(message: types.Message, state: FSMContext):
    await validate_number(message, state, BotStates.calc_extra, "price", "calc_extra")

@router.message(BotStates.calc_extra)
async def step_extra(message: types.Message, state: FSMContext):
    lang = await get_current_lang(message.from_user.id)
    try:
        commission = float(message.text.replace(',', '.'))
        if commission < 0: raise ValueError
        
        data = await state.get_data()
        
        # Расчет
        result = calculate_margin(
            data['cost'], data['delivery'], data['marketing'], 
            data['price'], commission
        )
        report = format_margin_report(result, lang)
        
        await message.answer(report, parse_mode="Markdown", reply_markup=get_main_keyboard(lang))
        await state.clear()
        
    except ValueError:
        await message.answer(get_text(lang, "calc_error"))


# === 6. ОТЛОВ НЕИЗВЕСТНЫХ СООБЩЕНИЙ ===

# Этот хэндлер должен быть последним, чтобы отловить все, что не поймано выше
@router.message()
async def unknown_message(message: types.Message, state: FSMContext):
    lang = await get_current_lang(message.from_user.id)
    
    # Если пользователь находится в каком-то состоянии, но ввел неверные данные
    current_state = await state.get_state()
    if current_state:
        # Просто повторяем предыдущий шаг (это грубо, но эффективно)
        await message.answer(get_text(lang, "calc_error")) 
        return
        
    # Если бот просто не знает, что ответить
    await message.answer(get_text(lang, "menu"), reply_markup=get_main_keyboard(lang))
