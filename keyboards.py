from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# ---------- Клавиатура выбора языка ----------
language_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Русский 🇷🇺"),
            KeyboardButton(text="Кыргызча 🇰🇬"),
            KeyboardButton(text="Қазақша 🇰🇿")
        ]
    ],
    resize_keyboard=True
)

# ---------- Главное меню ----------
main_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Анализ рынка 📊"),
            KeyboardButton(text="Подбор ниши 🧭")
        ],
        [
            KeyboardButton(text="Калькулятор маржи 💰"),
            KeyboardButton(text="Рекомендации ⚡")
        ],
        [
            KeyboardButton(text="Премиум 🚀")
        ]
    ],
    resize_keyboard=True
)
