import openai
from config import OPENAI_KEY
from messages_ru import texts as ru
from messages_kg import texts as kg
from messages_kz import texts as kz

openai.api_key = OPENAI_KEY

def get_texts(lang):
    if lang == "kg":
        return kg
    if lang == "kz":
        return kz
    return ru


async def ask_openai(lang, query):
    prompt = build_prompt(lang, query)

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message["content"]


def build_prompt(lang, query):
    if lang == "kg":
        return f"Жоопту кыргызча, ү, ө, ң тамгалары менен бер. Суроо: {query}"
    elif lang == "kz":
        return f"Жауапты қазақша ә, ғ, қ, ң, ө, ү, ұ, і әріптерімен бер. Сұрақ: {query}"
    return f"Ответь строго на русском языке. Вопрос: {query}"
