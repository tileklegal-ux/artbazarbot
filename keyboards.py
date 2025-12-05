from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


# Главное меню — универсальное, но текст зависит от языка
def main_menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    if lang == "ru":
        buttons = [
            [KeyboardButton(text="Анализ рынка 📊"), KeyboardButton(text="Подбор ниши 🧭")],
            [KeyboardButton(text="Калькулятор маржи 💰"), KeyboardButton(text="Рекомендации ⚡")],
            [KeyboardButton(text="Премиум 🚀")]
        ]
    elif lang == "kg":
        buttons = [
            [KeyboardButton(text="Базар анализи 📊"), KeyboardButton(text="Ниша тандоо 🧭")],
            [KeyboardButton(text="Маржа калькулятору 💰"), KeyboardButton(text="Сунуштар ⚡")],
            [KeyboardButton(text="Премиум 🚀")]
        ]
    elif lang == "kz":
        buttons = [
            [KeyboardButton(text="Нарық талдауы 📊"), KeyboardButton(text="Ниша таңдау 🧭")],
            [KeyboardButton(text="Маржа калькуляторы 💰"), KeyboardButton(text="Ұсыныстар ⚡")],
            [KeyboardButton(text="Премиум 🚀")]
        ]
    else:  
        # fallback — русский
        buttons = [
            [KeyboardButton(text="Анализ рынка 📊"), KeyboardButton(text="Подбор ниши 🧭")],
            [KeyboardButton(text="Калькулятор маржи 💰"), KeyboardButton(text="Рекомендации ⚡")],
            [KeyboardButton(text="Премиум 🚀")]
        ]

    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )
