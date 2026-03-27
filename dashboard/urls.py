from django.urls import path
from dashboard.views import GymDashboardView
from .web_views import owner_dashboard_page,update_branch_access_mode

urlpatterns = [
    path("gyms/<int:gym_id>/overview/", GymDashboardView.as_view()),
    path("app/gyms/<int:gym_id>/", owner_dashboard_page, name="owner_dashboard_page"),
    path("app/gyms/<int:gym_id>/settings/branch-access/",update_branch_access_mode,name="update_branch_settings"),
]



