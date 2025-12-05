import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from keyboards import main_menu_keyboard
from database import set_user_language, get_user_language
from openai_api import analyze_market, pick_niche, recommendations

router = Router()


# ---------------------------
#  START
# ---------------------------
@router.message(F.text == "/start")
async def start_cmd(message: Message):
    await message.answer(
        "Выберите язык / Тилди тандаңыз / Тілді таңдаңыз:",
        reply_markup=main_menu_keyboard("lang")
    )

    # Покажем язык-кнопки отдельно
    await message.answer(
        "Русский 🇷🇺\nКыргызча 🇰🇬\nҚазақша 🇰🇿"
    )


# ---------------------------
#  LANGUAGE SELECTION
# ---------------------------
@router.message(F.text.in_(["Русский 🇷🇺", "Кыргызча 🇰🇬", "Қазақша 🇰🇿"]))
async def set_language(message: Message):
    lang = "ru" if "Русский" in message.text else "kg" if "Кыргызча" in message.text else "kz"
    user_id = message.from_user.id

    set_user_language(user_id, lang)
    logging.info(f"User {user_id} set language: {lang}")

    if lang == "ru":
        await message.answer("Язык сохранён. Чем займёмся?", reply_markup=main_menu_keyboard("ru"))
    elif lang == "kg":
        await message.answer("Тилиңиз сакталды. Эмне жасайбыз?", reply_markup=main_menu_keyboard("kg"))
    else:
        await message.answer("Тіліңіз сақталды. Не істейміз?", reply_markup=main_menu_keyboard("kz"))


# ---------------------------
#  ANALYZE MARKET
# ---------------------------
@router.message(F.text.contains("Анализ рынка"))
async def ask_market(message: Message):
    await message.answer("Опиши товар или нишу, для которой нужен анализ рынка.")
    # сохраняем состояние
    await router.state.set_state("await_market")


@router.message(router.state == "await_market")
async def process_market(message: Message, state: FSMContext):
    text = message.text
    await message.answer("Думаю над ответом… Это может занять несколько секунд ⏳")

    result = await analyze_market(text)

    # очищаем состояние
    await state.clear()

    await message.answer(result)


# ---------------------------
#  PICK NICHE
# ---------------------------
@router.message(F.text.contains("Подбор ниши"))
async def ask_niche(message: Message):
    await message.answer("Опиши, чем хочешь заниматься. Я оценю нишу.")
    await router.state.set_state("await_niche")


@router.message(router.state == "await_niche")
async def process_niche(message: Message, state: FSMContext):
    text = message.text
    await message.answer("Секунду, думаю… ⏳")

    result = await pick_niche(text)

    await state.clear()
    await message.answer(result)


# ---------------------------
#  МARGIN CALCULATOR (пока заглушка)
# ---------------------------
@router.message(F.text.contains("Калькулятор маржи"))
async def margin_stub(message: Message):
    await message.answer("Калькулятор маржи скоро будет доступен в следующем обновлении.")


# ---------------------------
#  RECOMMENDATIONS
# ---------------------------
@router.message(F.text.contains("Рекомендации"))
async def ask_recommend(message: Message):
    await message.answer("Расскажи о товаре и ситуации — дам рекомендации по продажам.")
    await router.state.set_state("await_recommend")


@router.message(router.state == "await_recommend")
async def process_recommend(message: Message, state: FSMContext):
    text = message.text
    await message.answer("Обрабатываю запрос… ⏳")

    result = await recommendations(text)

    await state.clear()
    await message.answer(result)


# ---------------------------
#  PREMIUM (заглушка)
# ---------------------------
@router.message(F.text.contains("Премиум"))
async def premium(message: Message):
    await message.answer("Премиум-функции в разработке. Позже здесь появятся крутые инструменты.")
