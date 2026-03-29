from aiogram import types
from django.conf import settings
from asgiref.sync import sync_to_async

from telegram_bot.keyboards import kb_request_phone, kb_main_menu
from users.services import link_member_telegram  # keep your existing single-gym phone linking for now


def webapp_url() -> str:
    return f"{settings.WEBAPP_BASE_URL}/api/identifiers/app/member/qr/"


async def on_start(message: types.Message):
    await message.answer(
        "🇷🇺 Привет! 👋\n\n"
        "Этот бот используется для входа в зал через QR-код\n\n"
        "Нажмите кнопку «Меню», чтобы открыть свои залы\n\n"
        "🇺🇿 Salom! 👋\n\n"
        "Bu bot zalga QR orqali kirish uchun ishlatiladi\n\n"
        "Zallaringizni ochish uchun «Menu» tugmasini bosing"
    )


async def on_contact(message: types.Message):
    if not message.contact:
        return

    # v1: contact-linking still needs gym context to find Member.
    # BUT we no longer do it here. WebApp does cross-gym link by phone.
    # So just tell them to use WebApp link-phone.

    await message.answer(
        "Thanks ✅ Now open My QR and link your phone inside the WebApp.",
        reply_markup=kb_main_menu(webapp_url()),
    )


async def on_my_qr(message: types.Message):
    await message.answer("Opening…", reply_markup=kb_main_menu(webapp_url()))