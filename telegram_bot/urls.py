from django.urls import path
from telegram_bot.views import WebAppAuthView

urlpatterns = [
    path("webapp/auth/", WebAppAuthView.as_view()),
]