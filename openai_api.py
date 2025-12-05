import os
import asyncio
from openai import OpenAI
from database import get_user_language

# Инициализация клиента
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ---------- язык -> стиль ----------
def apply_style(text: str, lang: str) -> str:
    """Добавляем нужный стиль под язык пользователя."""
    if lang == "kg":
        style = (
            "Сен товардык бизнес боюнча профессионал консультантсың. "
            "Жооптор түшүнүктүү, ишенимдүү, жандуу тил менен. "
            "Тизмектерди, маркерленген пункттарды, Markdown жана '###' колдонбо. "
            "Жөн эле тынымсыз, түшүнүктүү текст менен жооп бер."
        )
    elif lang == "kz":
        style = (
            "Сен тауарлық бизнес бойынша кәсіби кеңесшісің. "
            "Жауаптарың сенімді, нақты, адамға түсінікті тілде. "
            "Тізімдерсіз, Markdown-сыз, '###' қолданба. "
            "Жай ғана біртұтас мәтін түрінде жауап бер."
        )
    else:  # ru по умолчанию
        style = (
            "Ты профессиональный консультант по товарному бизнесу. "
            "Отвечай живо, по-деловому и простым человеческим языком. "
            "Не используй списки, маркеры, Markdown и заголовки типа '###'. "
            "Ответ должен быть цельным текстом без пунктов."
        )

    return f"{style}\n\n{text}"


# ---------- общий быстрый вызов OpenAI ----------
async def _call_openai(prompt: str) -> str:
    """
    Вызываем OpenAI в отдельном потоке, чтобы не блокировать aiogram.
    """
    def _sync_request():
        return client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=260,      # поменьше токенов = быстрее ответ
            temperature=0.4,     # меньше креативности, больше скорость и стабильность
        )

    response = await asyncio.to_thread(_sync_request)

    # В новых версиях .message.content обычно уже строка
    content = response.choices[0].message.content
    # На всякий случай, если придёт список фрагментов
    if isinstance(content, list):
        parts = []
        for part in content:
            text = getattr(part, "text", None)
            if text:
                parts.append(text)
        return "".join(parts).strip()

    return str(content).strip()


# ---------- Анализ рынка ----------
async def analyze_market(query: str, user_id: int | None = None) -> str:
    lang = get_user_language(user_id) if user_id else "ru"

    prompt = apply_style(
        (
            f"Проанализируй рынок для товара или ниши: {query}. "
            "Коротко объясни, какой спрос, какая конкуренция и каковы перспективы. "
            "Говори как живой консультант, без пунктов и структурированных списков. "
            "Нужен понятный вывод: стоит ли в это заходить и на что обратить внимание."
        ),
        lang,
    )

    return await _call_openai(prompt)


# ---------- Оценка ниши ----------
async def pick_niche(query: str, user_id: int | None = None) -> str:
    lang = get_user_language(user_id) if user_id else "ru"

    prompt = apply_style(
        (
            f"Оцени бизнес-нишу: {query}. "
            "Скажи по-честному, есть ли смысл в неё заходить, "
            "в чём основные плюсы, какие слабые места и ключевые риски. "
            "Без списков, просто связный разбор и итог: стоит или не стоит, и при каких условиях."
        ),
        lang,
    )

    return await _call_openai(prompt)


# ---------- Рекомендации ----------
async def recommendations(query: str, user_id: int | None = None) -> str:
    lang = get_user_language(user_id) if user_id else "ru"

    prompt = apply_style(
        (
            f"Дай рекомендации по продажам товара или оффера: {query}. "
            "Представь, что к тебе пришёл предприниматель и просит честный разбор. "
            "Объясни, что ему делать с продуктом, позиционированием и каналами продаж. "
            "Говори простым, человеческим языком, без списков, как на личной консультации."
        ),
        lang,
    )

    return await _call_openai(prompt)
