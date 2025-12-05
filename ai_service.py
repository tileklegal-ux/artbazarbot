from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL

client = OpenAI(api_key=OPENAI_API_KEY)


def _call_openai(system_prompt: str, user_text: str) -> str:
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
        temperature=0.6,
        max_tokens=600,
    )
    return resp.choices[0].message.content.strip()


def analyze_market(user_text: str, lang: str) -> str:
    system = (
        "Ты — AI-ассистент для онлайн-продавцов. "
        "Делаешь короткий, структурированный анализ рынка по товару: "
        "1) Спрос, 2) Конкуренция, 3) Цены, 4) Риски, 5) Вывод и совет по запуску. "
        f"Отвечай на языке: {lang}."
    )
    return _call_openai(system, user_text)


def analyze_niche(user_text: str, lang: str) -> str:
    system = (
        "Ты — консультант по нишам для онлайн-бизнеса. "
        "Оцени нишу по пунктам: 1) Целевая аудитория, 2) Боль/проблема, "
        "3) Конкуренция, 4) Маржинальность, 5) Сложность входа, 6) Потенциал на 6 месяцев. "
        f"Отвечай на языке: {lang}."
    )
    return _call_openai(system, user_text)


def give_recommendations(user_text: str, lang: str) -> str:
    system = (
        "Ты — AI-ассистент по продажам. На основе описания товара и ситуации "
        "дай конкретные рекомендации: 1) Позиционирование, 2) Оффер, 3) Креативы, "
        "4) Каналы трафика, 5) Первые шаги. "
        f"Отвечай на языке: {lang}."
    )
    return _call_openai(system, user_text)
