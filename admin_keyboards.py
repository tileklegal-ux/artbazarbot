from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# ---------- Меню владельца ----------
owner_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Управление менеджерами"),
            KeyboardButton(text="Премиум-доступы"),
        ],
        [
            KeyboardButton(text="Статистика"),
            KeyboardButton(text="Перезапуск системы"),
        ],
        [
            KeyboardButton(text="Главное меню")
        ]
    ],
    resize_keyboard=True
)

# ---------- Меню менеджера ----------
manager_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Премиум-доступы"),
            KeyboardButton(text="Оплаты"),
        ],
        [
            KeyboardButton(text="Поддержка"),
            KeyboardButton(text="Главное меню"),
        ]
    ],
    resize_keyboard=True
)
