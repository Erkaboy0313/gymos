from aiogram import types

def kb_request_phone() -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="📱 Send phone number", request_contact=True)]],
        resize_keyboard=True,
    )

def kb_main_menu(webapp_url: str) -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="🧾 My QR", web_app=types.WebAppInfo(url=webapp_url))]],
        resize_keyboard=True,
    )