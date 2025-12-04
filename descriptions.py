# Генератор описаний товара

def generate_description(product_name: str, lang: str) -> str:
    templates = {
        "ru": f"✍️ Описание товара '{product_name}' будет доступно позже.",
        "kg": f"✍️ '{product_name}' товарын сүрөттөсө жакында болот.",
        "kz": f"✍️ '{product_name}' тауар сипаттамасы жақында дайын.",
    }
    return templates[lang]
