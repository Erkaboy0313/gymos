from django.urls import path
from devices.views import DeviceListCreateView, DeviceUpdateView

urlpatterns = [
    path("gyms/<int:gym_id>/devices/", DeviceListCreateView.as_view()),
    path("gyms/<int:gym_id>/devices/<int:device_id>/", DeviceUpdateView.as_view()),
]

from devices.web_view import devices_page, device_create, device_update

urlpatterns += [
    path("app/gyms/<int:gym_id>/devices/", devices_page),
    path("app/gyms/<int:gym_id>/devices/create/", device_create),
    path("app/gyms/<int:gym_id>/devices/<int:device_id>/update/", device_update),
]
