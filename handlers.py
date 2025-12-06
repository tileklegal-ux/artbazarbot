from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime

from keyboards import language_keyboard, get_main_keyboard
from database import set_user_language, get_user_language
from openai_api import analyze_market, pick_niche, recommendations
from roles_db import get_role
from premium_db import has_active_premium, get_premium


router = Router()


# ---------- FSM-состояния ----------
class UserStates(StatesGroup):
    await_market = State()
    await_niche = State()
    await_reco = State()


# ---------- Тексты по языкам ----------
def get_texts(user_id: int):
    lang = get_user_language(user_id) or "ru"

    if lang == "kg":
        return {
            "lang_chosen": "Тилди сактап койдум. Эми сен үчүн жардамчы болуп иштейм.",
            "welcome": (
                "ArtBazar AI'га кош келиңиз — онлайн сатуучулар үчүн жардамчы.\n\n"
                "Төмөндөн керектүү функцияны тандаңыз:"
            ),
            "ask_market": "Кайсы товар же ниша боюнча рынокту текшергибиз келет? Кыскача жаз.",
            "ask_niche": "Эмне менен алектенгиң келет? Кыскача сүрөттөп бер.",
            "ask_reco": "Товар жөнүндө жана кырдаалды сүрөттөп бер, сатуулар боюнча кеңеш берем.",
            "thinking": "Жооп даярдап жатам… Бул бир аз секундга созулушу мүмкүн ⏳",
            "margin_soon": "Маржа калькулятору кийинки жаңыланууда кошулат.",
            "premium_info_no": (
                "Азыр премиум жок. Премиумда ботто суроолор жок чектөөсүз.\n"
                "Тарифтер: 1 ай, 6 ай, 1 жыл — менеджерден же колдоо аркылуу билсең болот."
            ),
            "premium_info_yes": "Сенде активдүү премиум бар: {date} чейин. Пайдалана бер 🚀",
            "unknown": "Команданы түшүнгөн жокмун. Төмөнкү менюдан баскычтарды колдонуңуз.",
        }

    if lang == "kz":
        return {
            "lang_chosen": "Тілді сақтап қойдым. Енді саған ассистент ретінде жұмыс жасаймын.",
            "welcome": (
                "ArtBazar AI — онлайн сатушыларға арналған ассистент.\n\n"
                "Төменнен қажетті функцияны таңда:"
            ),
            "ask_market": "Қай тауар немесе ниша бойынша нарықты талдағымыз келеді? Қысқаша жаз.",
            "ask_niche": "Немен айналысқың келеді? Қысқаша сипаттап жаз.",
            "ask_reco": "Тауар және жағдай туралы жаз, сатылым бойынша кеңес беремін.",
            "thinking": "Жауап дайындап жатырмын… Бірнеше секунд кетуі мүмкін ⏳",
            "margin_soon": "Маржа калькуляторы келесі жаңартуда қосылады.",
            "premium_info_no": (
                "Қазір премиум қосылмаған. Премиумда сұрақтар санына шектеу жоқ.\n"
                "Тарифтер: 1 ай, 6 ай, 1 жыл — менеджерден біл."
            ),
            "premium_info_yes": "Сенде белсенді премиум бар: {date} дейін. Пайдалана бер 🚀",
            "unknown": "Команданы түсінбедім. Төмендегі менюдегі батырмаларды қолдан.",
        }

    # по умолчанию — русский
    return {
        "lang_chosen": "Я запомнил язык. Теперь буду отвечать для тебя как помощник-продавца.",
        "welcome": (
            "Добро пожаловать в ArtBazar AI — ассистент для продавцов онлайн.\n\n"
            "Выбери нужную функцию ниже:"
        ),
        "ask_market": "Опиши товар или нишу, для которой нужен анализ рынка.",
        "ask_niche": "Опиши, чем хочешь заниматься. Бот оценит нишу.",
        "ask_reco": "Расскажи о товаре и ситуации, дам рекомендации по продажам.",
        "thinking": "Думаю над ответом… Это может занять несколько секунд ⏳",
        "margin_soon": "Калькулятор маржи скоро будет доступен в следующем обновлении.",
        "premium_info_no": (
            "Сейчас премиум не активен. В премиум-доступе бот отвечает без ограничений.\n"
            "Тарифы: 1 месяц, 6 месяцев, 1 год — напиши менеджеру или в поддержку."
        ),
        "premium_info_yes": "У тебя активный премиум до {date}. Жми на кнопки — лимитов нет 🚀",
        "unknown": "Я не распознал команду. Пользуйся кнопками внизу.",
    }


# ---------- /start ----------
@router.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer(
        "Выберите язык / Тилди танданыз / Тілді таңдаңыз:",
        reply_markup=language_keyboard,
    )


# ---------- Установка языка + показ меню по роли ----------
@router.message(F.text == "Русский 🇷🇺")
async def set_lang_ru(message: Message):
    user_id = message.from_user.id
    set_user_language(user_id, "ru")
    t = get_texts(user_id)
    role = get_role(user_id)
    kb = get_main_keyboard(role)

    await message.answer(t["lang_chosen"])
    await message.answer(t["welcome"], reply_markup=kb)


@router.message(F.text == "Кыргызча 🇰🇬")
async def set_lang_kg(message: Message):
    user_id = message.from_user.id
    set_user_language(user_id, "kg")
    t = get_texts(user_id)
    role = get_role(user_id)
    kb = get_main_keyboard(role)

    await message.answer(t["lang_chosen"])
    await message.answer(t["welcome"], reply_markup=kb)


@router.message(F.text == "Қазақша 🇰🇿")
async def set_lang_kz(message: Message):
    user_id = message.from_user.id
    set_user_language(user_id, "kz")
    t = get_texts(user_id)
    role = get_role(user_id)
    kb = get_main_keyboard(role)

    await message.answer(t["lang_chosen"])
    await message.answer(t["welcome"], reply_markup=kb)


# ---------- Анализ рынка ----------
@router.message(F.text == "Анализ рынка 📊")
async def ask_market_question(message: Message, state: FSMContext):
    t = get_texts(message.from_user.id)
    await state.set_state(UserStates.await_market)
    await message.answer(t["ask_market"])


@router.message(UserStates.await_market)
async def handle_market_question(message: Message, state: FSMContext):
    t = get_texts(message.from_user.id)
    await message.answer(t["thinking"])

    answer = await analyze_market(message.text, user_id=message.from_user.id)
    await message.answer(answer)

    await state.clear()


# ---------- Подбор ниши ----------
@router.message(F.text == "Подбор ниши 🧭")
async def ask_niche_question(message: Message, state: FSMContext):
    t = get_texts(message.from_user.id)
    await state.set_state(UserStates.await_niche)
    await message.answer(t["ask_niche"])


@router.message(UserStates.await_niche)
async def handle_niche_question(message: Message, state: FSMContext):
    t = get_texts(message.from_user.id)
    await message.answer(t["thinking"])

    answer = await pick_niche(message.text, user_id=message.from_user.id)
    await message.answer(answer)

    await state.clear()


# ---------- Рекомендации ----------
@router.message(F.text == "Рекомендации ⚡")
async def ask_reco_question(message: Message, state: FSMContext):
    t = get_texts(message.from_user.id)
    await state.set_state(UserStates.await_reco)
    await message.answer(t["ask_reco"])


@router.message(UserStates.await_reco)
async def handle_reco_question(message: Message, state: FSMContext):
    t = get_texts(message.from_user.id)
    await message.answer(t["thinking"])

    answer = await recommendations(message.text, user_id=message.from_user.id)
    await message.answer(answer)

    await state.clear()


# ---------- Калькулятор маржи (заглушка) ----------
@router.message(F.text == "Калькулятор маржи 💰")
async def margin_stub(message: Message):
    t = get_texts(message.from_user.id)
    await message.answer(t["margin_soon"])


# ---------- Премиум ----------
@router.message(F.text == "Премиум 🚀")
async def premium_info(message: Message):
    t = get_texts(message.from_user.id)
    uid = message.from_user.id

    if has_active_premium(uid):
        until_ts, tariff = get_premium(uid)  # type: ignore
        dt = datetime.fromtimestamp(until_ts)
        date_str = dt.strftime("%d.%m.%Y")
        text = t["premium_info_yes"].format(date=date_str)
        text += f"\n\nТариф: {tariff}"
        await message.answer(text)
    else:
        await message.answer(t["premium_info_no"])


# ---------- Админ-кнопка для владельца ----------
@router.message(F.text == "Админ 👑")
async def admin_button(message: Message):
    role = get_role(message.from_user.id)
    if role != "owner":
        await message.answer("Эта зона только для владельца 👑.")
        return

    await message.answer(
        "👑 Админ-панель владельца. Здесь будут:\n"
        "- управление менеджерами\n"
        "- выдача премиума\n"
        "- просмотр статистики\n\n"
        "Пока это заглушка, но кнопка и роль работают."
    )


# ---------- Кнопка Менеджер 📋 ----------
@router.message(F.text == "Менеджер 📋")
async def manager_button(message: Message):
    role = get_role(message.from_user.id)
    if role not in ("manager", "owner"):
        await message.answer("Доступно только менеджеру и владельцу.")
        return

    await message.answer(
        "📋 Панель менеджера. Здесь будут:\n"
        "- работа с премиум-клиентами\n"
        "- фиксация оплат\n"
        "- поддержка клиентов\n\n"
        "Пока заглушка, но роль и интерфейс уже работают."
    )


# ---------- Любой другой текст ----------
@router.message()
async def fallback(message: Message):
    t = get_texts(message.from_user.id)
    role = get_role(message.from_user.id)
    kb = get_main_keyboard(role)
    await message.answer(t["unknown"], reply_markup=kb)
