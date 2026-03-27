from django.urls import path
from identifiers.views import MemberQRTokenView,MemberQRPageView,MemberWebAppView

urlpatterns = [
    # API
    path("member/qr-token/", MemberQRTokenView.as_view()),

    # WEB APP (single entry)
    path("app/member/qr/", MemberWebAppView.as_view()),
    path("gyms/<int:gym_id>/members/<int:member_id>/qr/", MemberQRPageView.as_view()),
]