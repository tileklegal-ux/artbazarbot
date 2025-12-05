from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from keyboards import main_menu_keyboard, language_keyboard
from database import set_user_language, get_user_language
from openai_api import analyze_market, pick_niche, recommendations


router = Router()


# ---------- FSM-состояния ----------
class UserStates(StatesGroup):
    await_market = State()
    await_niche = State()
    await_reco = State()


# ---------- тексты по языкам ----------
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
            "premium_soon": "Премиум-функциялар иштелип жатат. Кийин бул жерде күчтүү инструменттер болот.",
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
            "premium_soon": "Премиум-функциялар жасалып жатыр. Кейін мұнда мықты құралдар болады.",
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
        "premium_soon": "Премиум-функции в разработке. Позже сюда завезём жирные фишки.",
        "unknown": "Я не распознал команду. Пользуйся кнопками внизу.",
    }


# ---------- /start и выбор языка ----------
@router.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer(
        "Выберите язык / Тилди танданыз / Тілді таңдаңыз:",
        reply_markup=language_keyboard,
    )


@router.message(F.text == "Русский 🇷🇺")
async def set_lang_ru(message: Message):
    set_user_language(message.from_user.id, "ru")
    t = get_texts(message.from_user.id)
    await message.answer(t["lang_chosen"])
    await message.answer(t["welcome"], reply_markup=main_menu_keyboard)


@router.message(F.text == "Кыргызча 🇰🇬")
async def set_lang_kg(message: Message):
    set_user_language(message.from_user.id, "kg")
    t = get_texts(message.from_user.id)
    await message.answer(t["lang_chosen"])
    await message.answer(t["welcome"], reply_markup=main_menu_keyboard)


@router.message(F.text == "Қазақша 🇰🇿")
async def set_lang_kz(message: Message):
    set_user_language(message.from_user.id, "kz")
    t = get_texts(message.from_user.id)
    await message.answer(t["lang_chosen"])
    await message.answer(t["welcome"], reply_markup=main_menu_keyboard)


# ---------- Меню: Анализ рынка ----------
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


# ---------- Меню: Подбор ниши ----------
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


# ---------- Меню: Рекомендации ----------
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


# ---------- Меню: Калькулятор маржи (пока-заглушка) ----------
@router.message(F.text == "Калькулятор маржи 💰")
async def margin_stub(message: Message):
    t = get_texts(message.from_user.id)
    await message.answer(t["margin_soon"])


# ---------- Меню: Премиум (заглушка) ----------
@router.message(F.text == "Премиум 🚀")
async def premium_stub(message: Message):
    t = get_texts(message.from_user.id)
    await message.answer(t["premium_soon"])


# ---------- Любой другой текст ----------
@router.message()
async def fallback(message: Message):
    t = get_texts(message.from_user.id)
    await message.answer(t["unknown"], reply_markup=main_menu_keyboard)
