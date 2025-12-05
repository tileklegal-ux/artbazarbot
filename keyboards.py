from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


# Пользовательское меню
user_kb = ReplyKeyboardMarkup(
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


# Менеджерское меню
manager_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Панель менеджера 🧰"),
            KeyboardButton(text="Проверить премиум 🔍")
        ],
        [
            KeyboardButton(text="Выдать премиум 🎁")
        ],
        [
            KeyboardButton(text="Вернуться в меню пользователя ↩️")
        ]
    ],
    resize_keyboard=True
)


# Меню владельца
owner_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Статистика 📈"),
            KeyboardButton(text="Выдать премиум пользователю 👑")
        ],
        [
            KeyboardButton(text="Назначить менеджера 🛠"),
            KeyboardButton(text="Снять менеджера ❌")
        ],
        [
            KeyboardButton(text="Меню менеджера 🧰"),
            KeyboardButton(text="Меню пользователя ↩️")
        ]
    ],
    resize_keyboard=True
)


# Выбор языка
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
