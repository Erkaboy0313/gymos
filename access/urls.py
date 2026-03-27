from django.urls import path
from access.views import KioskValidateView,KioskPageView
from .web_views import recent_entries_page
from .views_devices import DeviceValidateView

urlpatterns = [
    path("gyms/<int:gym_id>/devices/<int:device_id>/kiosk/validate/", KioskValidateView.as_view()),
    path("gyms/<int:gym_id>/devices/<int:device_id>/kiosk/", KioskPageView.as_view(), name='kiosk_page'),
    path("app/gyms/<int:gym_id>/entries/", recent_entries_page, name="recent_entries_page"),
    path("device/validate/", DeviceValidateView.as_view()),
]