from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


owner_admin_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Выдать премиум 🎁")],
        [KeyboardButton(text="Список премиум 👥")],
        [KeyboardButton(text="Добавить менеджера ➕")],
        [KeyboardButton(text="Список менеджеров 📋")],
        [KeyboardButton(text="⬅️ В главное меню")],
    ],
    resize_keyboard=True,
)

manager_admin_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Выдать премиум 🎁")],
        [KeyboardButton(text="Список премиум 👥")],
        [KeyboardButton(text="Поддержка 💬")],
        [KeyboardButton(text="⬅️ В главное меню")],
    ],
    resize_keyboard=True,
)
