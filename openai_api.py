import os
from openai import OpenAI
from database import get_user_language

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ---------- язык -> стиль ----------
def apply_style(text: str, lang: str):
    if lang == "ru":
        style = (
            "Пиши профессионально, живо, человеческим языком, как эксперт-предприниматель. "
            "Без списков, без Markdown, без '###'. Просто связный текст."
        )
    elif lang == "kg":
        style = (
            "Профессионал, ишенимдүү, түшүндүрүүчү тон менен жаз. "
            "Маркер, тизмек, '###' колдонбо. Жөн гана түшүнүктүү сүйлөмдөр."
        )
    else:
        style = (
            "Кәсіби, сенімді, анық стильде жаз. Тізімдерсіз, Markdown-сыз. "
            "Біртұтас текст болсын."
        )

    return f"{style}\n\n{text}"


# ---------- Анализ рынка ----------
async def analyze_market(query: str, user_id: int = None):
    lang = get_user_language(user_id) if user_id else "ru"

    prompt = apply_style(
        f"Проанализируй рынок для: {query}. "
        "Дай оценку спроса, конкуренции и перспектив, но в человеческой форме.",
        lang
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=350
    )

    return response.choices[0].message["content"]


# ---------- Оценка ниши ----------
async def pick_niche(query: str, user_id: int = None):
    lang = get_user_language(user_id) if user_id else "ru"

    prompt = apply_style(
        f"Оцени нишу: {query}. Скажи, есть ли смысл заходить, "
        "какие сильные стороны и риски, но без списков.",
        lang
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=350
    )

    return response.choices[0].message["content"]


# ---------- Рекомендации ----------
async def recommendations(query: str, user_id: int = None):
    lang = get_user_language(user_id) if user_id else "ru"

    prompt = apply_style(
        f"Дай рекомендации по продажам товара: {query}. "
        "Объясняй как живой консультант, без формальных списков.",
        lang
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=350
    )

    return response.choices[0].message["content"]
