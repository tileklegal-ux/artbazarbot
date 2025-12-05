from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database import create_or_update_user, get_user, set_language
from utils import get_texts

router = Router()


# ===========================
#   СТАРТ КОМАНДА
# ===========================
@router.message(F.text == "/start")
async def start_cmd(message: Message):
    user_id = message.from_user.id

    create_or_update_user(
        user_id,
        message.from_user.username,
        message.from_user.first_name,
    )

    user = get_user(user_id)
    texts = get_texts(user["language"])

    await message.answer(
        texts["welcome"],
        reply_markup=texts["main_menu"]
    )


# ===========================
#   ВЫБОР ЯЗЫКА
# ===========================
@router.callback_query(F.data.startswith("lang_"))
async def change_language(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = callback.data.split("_")[1]

    set_language(user_id, lang)

    texts = get_texts(lang)

    await callback.message.edit_text(
        texts["language_changed"],
        reply_markup=texts["main_menu"]
    )


# ===========================
#   МЕНЮ: ПОДБОР НИШИ
# ===========================
@router.callback_query(F.data == "niche")
async def niche_handler(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    texts = get_texts(user["language"])

    await callback.message.answer(texts["niche_placeholder"])


# ===========================
#   МЕНЮ: АНАЛИЗ РЫНКА
# ===========================
@router.callback_query(F.data == "market")
async def market_handler(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    texts = get_texts(user["language"])

    await callback.message.answer(texts["market_placeholder"])


# ===========================
#   МЕНЮ: АНАЛИЗ КОНКУРЕНТОВ
# ===========================
@router.callback_query(F.data == "competitors")
async def competitors_handler(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    texts = get_texts(user["language"])

    await callback.message.answer(texts["competitors_placeholder"])


# ===========================
#   МЕНЮ: КАЛЬКУЛЯТОР МАРЖИ
# ===========================
@router.callback_query(F.data == "margin_calc")
async def margin_calc_handler(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    texts = get_texts(user["language"])

    await callback.message.answer(texts["margin_placeholder"])


# ===========================
#   МЕНЮ: ИДЕИ
# ===========================
@router.callback_query(F.data == "ideas")
async def ideas_handler(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    texts = get_texts(user["language"])

    await callback.message.answer(texts["ideas_placeholder"])
