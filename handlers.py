from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from keyboards import user_kb, manager_kb, owner_kb, language_keyboard
from database import set_user_language, get_user_language
from roles_db import get_role, set_role
from openai_api import analyze_market, pick_niche, recommendations


router = Router()


# -------------------- FSM --------------------
class UserStates(StatesGroup):
    await_market = State()
    await_niche = State()
    await_reco = State()


# -------------------- Тексты --------------------
def t(user_id):
    lang = get_user_language(user_id) or "ru"

    texts_ru = {
        "lang_set": "Я запомнил язык!",
        "welcome": "Добро пожаловать в ArtBazar AI — ассистент для продавцов онлайн.\nВыбери нужную функцию ниже:",
        "ask_market": "Опиши товар или нишу для анализа:",
        "ask_niche": "Опиши нишу, которую хочешь оценить:",
        "ask_reco": "Расскажи о товаре и ситуации:",
        "thinking": "Думаю над ответом… секунду ⏳",
        "premium_soon": "Премиум развивается. Скоро добавим.",
        "unknown": "Не понял. Используй кнопки :)"
    }

    texts_kg = {
        "lang_set": "Тилди сактап койдум!",
        "welcome": "ArtBazar AI'га кош келдиңиз.\nФункция тандаңыз:",
        "ask_market": "Товар же нишаны сүрөттөп бер:",
        "ask_niche": "Ниша жөнүндө жаз:",
        "ask_reco": "Товар жөнүндө жаз:",
        "thinking": "Жооп даярдалууда… ⏳",
        "premium_soon": "Премиум иштелүүдө.",
        "unknown": "Түшүнгөн жокмун."
    }

    texts_kz = {
        "lang_set": "Тілді сақтап қойдым!",
        "welcome": "ArtBazar AI — сатушыларға арналған ассистент.",
        "ask_market": "Тауар немесе нишаны сипатта:",
        "ask_niche": "Ниша туралы жаз:",
        "ask_reco": "Тауар туралы жаз:",
        "thinking": "Жауап дайындалуда… ⏳",
        "premium_soon": "Премиум жасалып жатыр.",
        "unknown": "Түсінбедім."
    }

    return {"ru": texts_ru, "kg": texts_kg, "kz": texts_kz}.get(lang, texts_ru)


# -------------------- Команды --------------------
@router.message(F.text == "/start")
async def start(message: Message):
    await message.answer("Выберите язык:", reply_markup=language_keyboard)


@router.message(F.text == "Русский 🇷🇺")
async def set_ru(message: Message):
    set_user_language(message.from_user.id, "ru")
    await message.answer(t(message.from_user.id)["lang_set"])
    await show_menu(message)


@router.message(F.text == "Кыргызча 🇰🇬")
async def set_kg(message: Message):
    set_user_language(message.from_user.id, "kg")
    await message.answer(t(message.from_user.id)["lang_set"])
    await show_menu(message)


@router.message(F.text == "Қазақша 🇰🇿")
async def set_kz(message: Message):
    set_user_language(message.from_user.id, "kz")
    await message.answer(t(message.from_user.id)["lang_set"])
    await show_menu(message)


# -------------------- Меню по роли --------------------
async def show_menu(message: Message):
    role = get_role(message.from_user.id)

    if role == "owner":
        await message.answer("Меню владельца 🔥", reply_markup=owner_kb)

    elif role == "manager":
        await message.answer("Меню менеджера 👨‍💻", reply_markup=manager_kb)

    else:
        await message.answer(t(message.from_user.id)["welcome"], reply_markup=user_kb)


@router.message(F.text == "Назад ↩️")
async def back_to_user_menu(message: Message):
    set_role(message.from_user.id, "user")
    await show_menu(message)


# -------------------- Анализ рынка --------------------
@router.message(F.text == "Анализ рынка 📊")
async def ask_market(message: Message, state: FSMContext):
    await state.set_state(UserStates.await_market)
    await message.answer(t(message.from_user.id)["ask_market"])


@router.message(UserStates.await_market)
async def process_market(message: Message, state: FSMContext):
    await message.answer(t(message.from_user.id)["thinking"])
    answer = await analyze_market(message.text, message.from_user.id)
    await message.answer(answer)
    await state.clear()


# -------------------- Ниша --------------------
@router.message(F.text == "Подбор ниши 🧭")
async def ask_niche(message: Message, state: FSMContext):
    await state.set_state(UserStates.await_niche)
    await message.answer(t(message.from_user.id)["ask_niche"])


@router.message(UserStates.await_niche)
async def process_niche(message: Message, state: FSMContext):
    await message.answer(t(message.from_user.id)["thinking"])
    answer = await pick_niche(message.text, message.from_user.id)
    await message.answer(answer)
    await state.clear()


# -------------------- Рекомендации --------------------
@router.message(F.text == "Рекомендации ⚡")
async def ask_reco(message: Message, state: FSMContext):
    await state.set_state(UserStates.await_reco)
    await message.answer(t(message.from_user.id)["ask_reco"])


@router.message(UserStates.await_reco)
async def process_reco(message: Message, state: FSMContext):
    await message.answer(t(message.from_user.id)["thinking"])
    answer = await recommendations(message.text, message.from_user.id)
    await message.answer(answer)
    await state.clear()


# -------------------- Премиум временно --------------------
@router.message(F.text == "Премиум 🚀")
async def premium_temp(message: Message):
    await message.answer(t(message.from_user.id)["premium_soon"])
