from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from messages_ru import ru_texts
from messages_kg import kg_texts
from messages_kz import kz_texts


def get_texts(lang: str):
    if lang == "kg":
        return kg_texts
    if lang == "kz":
        return kz_texts
    return ru_texts  # язык по умолчанию — русский


def main_menu_buttons(texts):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=texts["btn_niche"], callback_data="niche")],
            [InlineKeyboardButton(text=texts["btn_market"], callback_data="market")],
            [InlineKeyboardButton(text=texts["btn_competitors"], callback_data="competitors")],
            [InlineKeyboardButton(text=texts["btn_margin"], callback_data="margin_calc")],
            [InlineKeyboardButton(text=texts["btn_ideas"], callback_data="ideas")],
            [InlineKeyboardButton(text=texts["btn_language"], callback_data="lang_menu")],
        ]
    )


def language_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
            [InlineKeyboardButton(text="🇰🇬 Кыргызча", callback_data="lang_kg")],
            [InlineKeyboardButton(text="🇰🇿 Қазақша", callback_data="lang_kz")],
        ]
    )
