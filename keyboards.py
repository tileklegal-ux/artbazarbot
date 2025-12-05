from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# ▶️ Пользовательское меню
user_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton("Анализ рынка 📊"), KeyboardButton("Подбор ниши 🧭")],
        [KeyboardButton("Калькулятор маржи 💰"), KeyboardButton("Рекомендации ⚡")],
        [KeyboardButton("Премиум 🚀")]
    ],
    resize_keyboard=True
)

# ▶️ Менеджерское меню
manager_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton("Проверить премиум 💎"), KeyboardButton("Отметить оплату 💵")],
        [KeyboardButton("Поддержка 🛟")],
        [KeyboardButton("Назад ↩️")]
    ],
    resize_keyboard=True
)

# ▶️ Меню владельца
owner_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton("Статистика 📊"), KeyboardButton("Пользователи 👤")],
        [KeyboardButton("Управление премиумом 💎"), KeyboardButton("Менеджеры 👨‍💻")],
        [KeyboardButton("Назад ↩️")]
    ],
    resize_keyboard=True
)

# ▶️ Кнопки выбора языка
language_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton("Русский 🇷🇺")],
        [KeyboardButton("Кыргызча 🇰🇬")],
        [KeyboardButton("Қазақша 🇰🇿")]
    ],
    resize_keyboard=True
)
