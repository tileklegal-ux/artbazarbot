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
            "lang_chosen": "Тилди сактап койдум. Эми товардык бизнес боюнча ассистент болуп иштейм.",
            "welcome": (
                "ArtBazar AI'га кош келиңиз 👋\n\n"
                "Бул бот сатуучуларга жардам берүү үчүн жасалган. Төмөнкү менюдан функция танда."
            ),
            "ask_market": "Кайсы товар же ниша боюнча рынокту талдайбыз? Кыскача жаз:",
            "ask_niche": "Кайсы ниша тууралуу ойлонуп жатасың? Кыскача жазып көр.",
            "ask_reco": "Товарыңды жана жагдайды сүрөттөп жаз, сатуу боюнча кеңеш берем:",
            "thinking": "Жооп даярдап жатам… Бир аз күтө тур 🔄",
            "margin_soon": "Маржа калькулятору кийинки жаңыртууда чыгат. Азырынча анализ жана кеңешти колдоно бер.",
            "premium_info_no": (
                "Премиум азыр активдүү эмес.\n\n"
                "Базалык режимде бардык функция ачык, бирок күнүнө 3 суроо лимит бар.\n\n"
                "Премиумда:\n"
                "• чексиз суроолор\n"
                "• тереңирээк анализ\n"
                "• приоритеттүү жооптор\n\n"
                "Тарифтер:\n"
                "• 1 ай — 490 сом\n"
                "• 6 ай — 1990 сом\n"
                "• 1 жыл — 2990 сом\n\n"
                "Сатып алуу үчүн менеджерге жаз:\n"
                "@Artbazar_support"
            ),
            "premium_info_yes": "Сендe активдүү премиум бар: {date} чейин. Колдонуп жүр 🚀",
            "unknown": "Түшүнгөн жокмун. Төмөнкү менюдагы баскычтардын бирин танда.",
        }

    if lang == "kz":
        return {
            "lang_chosen": "Тілді сақтап қойдым. Енді саған сатушы ассистенті ретінде жауап берем.",
            "welcome": (
                "ArtBazar AI — онлайн сатушыларға ассистент 👋\n\n"
                "Төмендегі мәзірден қажетті функцияны таңда."
            ),
            "ask_market": "Қай тауар немесе ниша бойынша нарықты талдаймыз? Қысқаша жазыңыз:",
            "ask_niche": "Қай нишамен айналысқыңыз келеді? Қысқаша сипаттаңыз:",
            "ask_reco": "Өнімді және жағдайды сипаттап жазыңыз, сатылым бойынша кеңес беремін:",
            "thinking": "Жауап дайындап жатырмын… Бірaz күте тұрыңыз ⏳",
            "margin_soon": "Маржа калькуляторы келесі жаңартуда қосылады. Қазір талдау мен ұсыныстарды қолдана бер.",
            "premium_info_no": (
                "Премиум қосылмаған.\n\n"
                "Базалық режимде барлық функция ашық, бірақ күніне 3 сұрақ лимит бар.\n\n"
                "Премиум режимде:\n"
                "• шексіз сұрақтар\n"
                "• терең талдау\n"
                "• приоритетті жауаптар\n\n"
                "Тарифтер:\n"
                "• 1 ай — 490 сом\n"
                "• 6 ай — 1990 сом\n"
                "• 1 жыл — 2990 сом\n\n"
                "Сатып алу үшін менеджерге жазыңыз:\n"
                "@Artbazar_support"
            ),
            "premium_info_yes": "Сізде белсенді премиум бар: {date} дейін. Пайдалана беріңіз 🚀",
            "unknown": "Команданы түсінбедім. Төмендегі мәзірден таңдаңыз.",
        }

    # ru по умолчанию
    return {
        "lang_chosen": "Я запомнил язык. Теперь буду отвечать как ассистент по товарному бизнесу.",
        "welcome": (
            "Добро пожаловать в ArtBazar AI 👋\n\n"
            "Это ассистент для онлайн-продавцов. Выбери нужную функцию в меню ниже."
        ),
        "ask_market": "Опиши товар или нишу, по которой нужен анализ рынка:",
        "ask_niche": "Опиши нишу, которую рассматриваешь. Я честно оценю перспективы:",
        "ask_reco": "Опиши товар и ситуацию — дам рекомендации по продажам:",
        "thinking": "Думаю над ответом… Это может занять несколько секунд ⏳",
        "margin_soon": "Калькулятор маржи скоро появится. Пока можешь использовать анализ и рекомендации.",
        "premium_info_no": (
            "Премиум у тебя пока не активирован.\n\n"
            "В базовом режиме доступны все функции, но есть лимит — 3 запроса в сутки.\n\n"
            "Премиум даёт:\n"
            "• безлимитные запросы\n"
            "• более глубокий разбор\n"
            "• приоритетные ответы\n\n"
            "Тарифы:\n"
            "• 1 месяц — 490 сом\n"
            "• 6 месяцев — 1990 сом\n"
            "• 1 год — 2990 сом\n\n"
            "Чтобы подключить премиум, напиши менеджеру:\n"
            "@Artbazar_support"
        ),
        "premium_info_yes": "У тебя активен премиум до {date}. Пользуйся на максимум 🚀",
        "unknown": "Не понял команду. Пожалуйста, используй кнопки меню.",
    }


# ---------------- СТАРТ И ЯЗЫК ----------------

@router.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer("Выберите язык:", reply_markup=language_keyboard)


@router.message(F.text.in_(["Русский 🇷🇺", "Кыргызча 🇰🇬", "Қазақша 🇰🇿"]))
async def set_language(message: Message, state: FSMContext):
    mapping = {
        "Русский 🇷🇺": "ru",
        "Кыргызча 🇰🇬": "kg",
        "Қазақша 🇰🇿": "kz",
    }

    lang = mapping[message.text]
    set_user_language(message.from_user.id, lang)

    t = get_texts(message.from_user.id)
    role = get_role(message.from_user.id)

    await state.clear()
    await message.answer(t["lang_chosen"])
    await message.answer(t["welcome"], reply_markup=get_main_keyboard(role))


@router.message(F.text == "🌐 Сменить язык")
async def change_language(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Выберите язык:", reply_markup=language_keyboard)


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


# ---------------- КАЛЬКУЛЯТОР МАРЖИ (СТАБ) ----------------

@router.message(F.text == "Калькулятор маржи 💰")
async def margin_stub(message: Message):
    t = get_texts(message.from_user.id)
    await message.answer(t["margin_soon"])


# ---------------- ПРЕМИУМ ----------------

@router.message(F.text == "Премиум 🚀")
async def premium_block(message: Message):
    uid = message.from_user.id
    t = get_texts(uid)

    if has_active_premium(uid):
        until_ts, tariff = get_premium(uid)
        if until_ts:
            date = datetime.fromtimestamp(until_ts).strftime("%d.%m.%Y")
            await message.answer(t["premium_info_yes"].format(date=date))
        else:
            await message.answer(t["premium_info_yes"].format(date="—"))
        return

    await message.answer(t["premium_info_no"], parse_mode="Markdown")


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
